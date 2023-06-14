# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

""" Library of code for status logs reused across various calling features """
import os
from datetime import datetime
import base64
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from enum import Enum


class State(Enum):
    STARTED = "Processing"
    COMPLETE = "Complete"
    ERROR = "Error"

class StatusClassification(Enum):
    DEBUG = "Debug"
    INFO = "Info"
    ERROR = "Error"


class StatusLog:

    def __init__(self, url, key, database_name, container_name):
        self._url = url
        self._key = key
        self._database_name = database_name
        self._container_name = container_name
        self._state = ""
        self._state_description = ""
                
        self.cosmos_client = CosmosClient(url=self._url, credential=self._key)

        # Select a database (will create it if it doesn't exist)
        self.database = self.cosmos_client.get_database_client(self._database_name)
        if self._database_name not in [db['id'] for db in self.cosmos_client.list_databases()]:
            self.database = self.cosmos_client.create_database(self._database_name)

        # Select a container (will create it if it doesn't exist)
        self.container = self.database.get_container_client(self._container_name)
        if self._container_name not in [container['id'] for container in self.database.list_containers()]:
            self.container = self.database.create_container(id=self._container_name, 
                partition_key=PartitionKey(path="/file_name"))
        
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: State):
        self._state = value
        
    @property
    def state_description(self):
        return self._state

    @state_description.setter
    def state_description(self, value):
        self._state_description = value               
               
        
    def encode_document_id(self, document_id):
        """ encode a path/file name to remove unsafe chars for a cosmos db id """
        safe_id = base64.urlsafe_b64encode(document_id.encode()).decode()
        return safe_id
        

    def upsert_document(self, document_path, status, status_classification: StatusClassification, fresh_start=False):
        """ Function to upsert a status item for a specified id """
        base_name = os.path.basename(document_path)
        document_id = self.encode_document_id(document_path)
        
        # If this event is the start of an upload, remove any existing status files for this path
        if fresh_start == True:
            try:
                self.container.delete_item(item=document_id, partition_key=base_name)
            except exceptions.CosmosResourceNotFoundError:
                pass

        json_document = ""
        try:
            # if the document exists then update it        
            json_document = self.container.read_item(item=document_id, partition_key=base_name)
            
            # Check if there has been a state change, and therefore to update state
            if json_document['state'] != str(self._state.value):
                json_document['state'] = str(self._state.value)
                json_document['state_description'] = self._state_description
                json_document['state_timestamp'] = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Append a new item to the array
            status_updates = json_document["status_updates"]     
            new_item = {
                "status": status,
                "status_timestamp": str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                "status_classification": str(status_classification.value)
            }
            status_updates.append(new_item)

        except Exception:
            # if this is a new document
            json_document = {
                "id": document_id,
                "file_path": document_path,
                "file_name": base_name,
                "state": str(self._state.value),
                "state_description": "",
                "state_timestamp": str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                "status_updates": [
                    {
                        "status": status,
                        "status_timestamp": str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        "status_classification": str(status_classification.value)
                    }
                ]
            }

        self.container.upsert_item(body=json_document)