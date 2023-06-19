import logging
import azure.functions as func
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
from azure.storage.queue import QueueClient, TextBase64EncodePolicy
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
POLLING_BACKOFF = 5


def main(msg: func.QueueMessage) -> None:
    logging.info('Python queue trigger function processed a queue item: %s',
                 msg.get_body().decode('utf-8'))

    # Receive message from the queue
    message_body = msg.get_body().decode('utf-8')
    message_json = json.loads(message_body)
    blob_path =  message_json['blob_name']
    FR_resultId = message_json['FR_resultId']
    queued_count = message_json['polling_queue_count']      
    
    statusLog.upsert_document(blob_path, 'Polling Form Recognizer', StatusClassification.INFO)
    statusLog.upsert_document(blob_path, 'Queue message received from pdf polling queue', StatusClassification.DEBUG)
    
    # Construct and submmit the polling message to FR
    headers = {
        'Ocp-Apim-Subscription-Key': FR_key
    }

    params = {
        'api-version': api_version
    }
    url = f"{endpoint}formrecognizer/documentModels/{FR_MODEL}/analyzeResults/{FR_resultId}"
    response = requests.get(url, headers=headers, params=params)
    statusLog.upsert_document(blob_path, 'FR response received', StatusClassification.DEBUG)
        
    # Check response and process
    if response.status_code == 200:
        # FR processing is complete OR still running- create document map 
        response_json = response.json()
        response_status = response_json['status']
        if response_status == "succeeded":
            # successful, so continue to document map and chunking
            statusLog.upsert_document(blob_path, f'Form Recognizer processing was successful', StatusClassification.INFO)  
            
        elif response_status == "running":
            # still running so requeue with a backoff
            if queued_count < MAX_REQUEUE_COUNT:
                backoff = POLLING_BACKOFF * (queued_count ** 2)
                backoff += random.randint(0, 10)
                queued_count += 1
                message_json['polling_queue_count'] = queued_count
                statusLog.upsert_document(blob_path, f"FR has not completed processing, requeuing. Back off of {backoff} seconds", StatusClassification.DEBUG) 
                queue_client = QueueClient.from_connection_string(azure_blob_connection_string, queue_name=pdf_polling_queue, message_encode_policy=TextBase64EncodePolicy())   
                message_json_str = json.dumps(message_json)  
                queue_client.send_message(message_json_str, visibility_timeout=backoff)       
            else:
                statusLog.upsert_document(blob_path, f'maximum submissions to FR reached', StatusClassification.ERROR, State.ERROR)        
        
        else:
            # unexpected status returned by FR
            statusLog.upsert_document(blob_path, f'unhandled response from form Recognizer - {response.text}', StatusClassification.ERROR, State.ERROR)  
                          
    else:
        statusLog.upsert_document(blob_path, f'Error raised by FR polling', StatusClassification.ERROR, State.ERROR) 

    
    
    