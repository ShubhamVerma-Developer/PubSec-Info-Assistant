import logging

import azure.functions as func
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.queue import QueueClient
import logging
import os
from enum import Enum
from shared_code.status_log import StatusLog, State, StatusClassification

azure_blob_storage_account = os.environ["BLOB_STORAGE_ACCOUNT"]
azure_blob_drop_storage_container = os.environ["BLOB_STORAGE_ACCOUNT_UPLOAD_CONTAINER_NAME"]
azure_blob_content_storage_container = os.environ["BLOB_STORAGE_ACCOUNT_OUTPUT_CONTAINER_NAME"]
azure_blob_storage_key = os.environ["BLOB_STORAGE_ACCOUNT_KEY"]
azure_blob_log_storage_container = os.environ["BLOB_STORAGE_ACCOUNT_LOG_CONTAINER_NAME"]
azure_blob_connection_string = os.environ["BLOB_CONNECTION_STRING"]
cosmosdb_url = os.environ["COSMOSDB_URL"]
cosmosdb_key = os.environ["COSMOSDB_KEY"]
cosmosdb_database_name = os.environ["COSMOSDB_DATABASE_NAME"]
cosmosdb_container_name = os.environ["COSMOSDB_CONTAINER_NAME"]
non_pdf_submit_queue = os.environ["NON_PDF_SUBMIT_QUEUE"]
pdf_polling_queue = os.environ["PDF_POLLING_QUEUE"]
pdf_submit_queue = os.environ["PDF_SUBMIT_QUEUE"]

statusLog = StatusLog(cosmosdb_url, cosmosdb_key, cosmosdb_database_name, cosmosdb_container_name)


def main(myblob: func.InputStream):
    """ Function to read PDF files and pass to the correct queue for processing"""
    statusLog.state = State.STARTED
    statusLog.upsert_document(myblob.name, 'File Uploaded', StatusClassification.INFO, True)    
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")
    
    statusLog.upsert_document(myblob.name, 'FileUploadedFunc function started', StatusClassification.DEBUG)    
    
    # Create message structure to send to queue
    try:
       
        file_extension = os.path.splitext(myblob.name)[1][1:].lower()     
        if file_extension == 'pdf':
             # If the file is a PDF a message is sent to the PDF processing queue.
            queue_name = pdf_submit_queue
  
        elif file_extension in ['htm', 'html', 'docx']:
            # Else a message is sent to the non PDF processing queue
            queue_name = non_pdf_submit_queue
                 
        else:
            # Unknown file type
            logging.info("Unknown file type")
            statusLog.state = State.ERROR
            error_message = f"Unexpected file type submitted {file_extension}"
            statusLog.state_description = error_message
            statusLog.upsert_document(myblob.name, error_message, StatusClassification.ERROR) 
            raise Exception(error_message)    
        
        # Create message
        message = {
            "blob_name": myblob.name,
            "queued_count": 1
        }        
        
        # Queue message
        queue_client = QueueClient.from_connection_string(azure_blob_connection_string, queue_name)   
        queue_client.send_message(message)
        statusLog.upsert_document(myblob.name, f'{file_extension} file queued for by function FileUploadedFunc', StatusClassification.DEBUG)          
        
    except Exception as e:
        statusLog.state = State.ERROR
        statusLog.state_description = str(e)
        statusLog.upsert_document(myblob.name, f"An error occurred - {str(e)}", StatusClassification.ERROR)
        raise