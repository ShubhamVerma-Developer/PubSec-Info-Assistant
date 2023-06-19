import logging
import azure.functions as func
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.queue import QueueClient
import logging
import os
from enum import Enum
from decimal import Decimal
import json
import requests
from shared_code.status_log import StatusLog, State, StatusClassification
from shared_code.utilities import Utilities
import random


azure_blob_storage_account = os.environ["BLOB_STORAGE_ACCOUNT"]
azure_blob_drop_storage_container = os.environ["BLOB_STORAGE_ACCOUNT_UPLOAD_CONTAINER_NAME"]
azure_blob_content_storage_container = os.environ["BLOB_STORAGE_ACCOUNT_OUTPUT_CONTAINER_NAME"]
azure_blob_storage_key = os.environ["BLOB_STORAGE_ACCOUNT_KEY"]
azure_blob_connection_string = os.environ["BLOB_CONNECTION_STRING"]
XY_ROUNDING_FACTOR = int(os.environ["XY_ROUNDING_FACTOR"])
CHUNK_TARGET_SIZE = int(os.environ["CHUNK_TARGET_SIZE"])
REAL_WORDS_TARGET = Decimal(os.environ["REAL_WORDS_TARGET"])
FR_API_VERSION = os.environ["FR_API_VERSION"]
# ALL or Custom page numbers for multi-page documents(PDF/TIFF). Input the page numbers and/or
# ranges of pages you want to get in the result. For a range of pages, use a hyphen, like pages="1-3, 5-6".
# Separate each page number or range with a comma.
TARGET_PAGES = os.environ["TARGET_PAGES"]
azure_blob_connection_string = os.environ["BLOB_CONNECTION_STRING"]
cosmosdb_url = os.environ["COSMOSDB_URL"]
cosmosdb_key = os.environ["COSMOSDB_KEY"]
cosmosdb_database_name = os.environ["COSMOSDB_DATABASE_NAME"]
cosmosdb_container_name = os.environ["COSMOSDB_CONTAINER_NAME"]
non_pdf_submit_queue = os.environ["NON_PDF_SUBMIT_QUEUE"]
pdf_polling_queue = os.environ["PDF_POLLING_QUEUE"]
pdf_submit_queue = os.environ["PDF_SUBMIT_QUEUE"]
endpoint = os.environ["AZURE_FORM_RECOGNIZER_ENDPOINT"]
FR_key = os.environ["AZURE_FORM_RECOGNIZER_KEY"]
api_version = os.environ["FR_API_VERSION"]


statusLog = StatusLog(cosmosdb_url, cosmosdb_key, cosmosdb_database_name, cosmosdb_container_name)
utilities = Utilities(azure_blob_storage_account, azure_blob_drop_storage_container, azure_blob_content_storage_container, azure_blob_storage_key)
FR_MODEL = "prebuilt-layout"
MAX_REQUEUE_COUNT = 5   #max times we will retry the submission


def main(msg: func.QueueMessage) -> None:
    logging.info('Python queue trigger function processed a queue item: %s',
                 msg.get_body().decode('utf-8'))

    # Receive message from the queue
    message_body = msg.get_body().decode('utf-8')
    message_json = json.loads(message_body)
    blob_path =  message_json['blob_name']
    queued_count =  message_json['queued_count']
    statusLog.upsert_document(blob_path, 'Subitting to Form Regignizer', StatusClassification.INFO)
    statusLog.upsert_document(blob_path, 'Queue message received from pdf submit queue', StatusClassification.DEBUG)

    # construct blob url
    blob_path_plus_sas = utilities.get_blob_and_sas(blob_path)
    statusLog.upsert_document(blob_path, 'SAS token generated', StatusClassification.DEBUG)

    # Construct and submmit the message to FR
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': FR_key
    }

    params = {
        'api-version': api_version
    }
    
    body = {
         "urlSource": blob_path_plus_sas
    }
    url = f"{endpoint}formrecognizer/documentModels/{FR_MODEL}:analyze"
 
    # Send the HTTP POST request with headers, query parameters, and request body
    response = requests.post(url, headers=headers, params=params, json=body)

    # Check if the request was successful (status code 200)
    if response.status_code == 202:
        # Successfully submitted
        statusLog.upsert_document(blob_path, 'PDF submitted to FR successfully', StatusClassification.DEBUG) 
        message_json['FR_resultId'] = response.headers.get("apim-request-id")         
        queue_client = QueueClient(account_url=f"https://{azure_blob_storage_account}.queue.core.windows.net", 
                                queue_name=pdf_polling_queue, 
                                credential=azure_blob_storage_key)    
        queue_client.send_message(message_json, visibility_timeout=0)      

    elif response.status_code == 429:
        # throttled, so requeue with random backoff seconds to mitigate throttling, unless it has hit the max tries
        if queued_count < MAX_REQUEUE_COUNT:
            max_seconds = 60 * (queued_count ** 2)
            max_seconds = max_seconds * queued_count
            backoff =  random.randint(1, max_seconds)
            queued_count += 1
            message_json['queued_count'] = queued_count
            statusLog.upsert_document(blob_path, f"Throttled on PDF submission to FR, requeuing. Back off of {backoff} seconds", StatusClassification.DEBUG) 
            queue_client = QueueClient(account_url=f"https://{azure_blob_storage_account}.queue.core.windows.net", 
                                    queue_name=pdf_submit_queue, 
                                    credential=azure_blob_storage_key)     
            queue_client.send_message(message_json, visibility_timeout=backoff)
        else:
            statusLog.upsert_document(blob_path, f'maximum submissions to FR reached', StatusClassification.ERROR, State.ERROR) 

    else:
        # general error occurred
        statusLog.upsert_document(blob_path, f'Error on PDF submission to FR - {response.code} {response.message}', StatusClassification.ERROR, State.ERROR) 