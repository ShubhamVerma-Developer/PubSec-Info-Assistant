""" Python function to read PDF files and extract text using Azure Form Recognizer"""

import logging
import os
from enum import Enum
from datetime import datetime, timedelta
import tiktoken
import nltk
nltk.download('words')
nltk.download('punkt')
import azure.functions as func
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.exceptions import HttpResponseError

XY_ROUNDING_FACTOR = 1
CHUNK_TARGET_SIZE = 750
REAL_WORDS_TARGET = 0.25
TARGET_PAGES = "ALL"            # ALL or Custom page numbers for multi-page documents(PDF/TIFF).
                                # Input the page numbers and/or ranges of pages you want to get
                                # in the result. For a range of pages, use a hyphen, like
                                # pages="1-3, 5-6". Separate each page number or range with a comma.

def main(myblob: func.InputStream):
    """ Function to read PDF files and extract text using Azure Form Recognizer"""
    logging.info("Python blob trigger function processed blob \n"
                 "Name: %s\n"
                 "Blob Size: %s bytes", myblob.name, myblob.length)

    try:
        
        analyze_layout(myblob)
    except HttpResponseError as error:
        print("For more information about troubleshooting errors, see the following guide: "
              "https://aka.ms/azsdk/python/formrecognizer/troubleshooting")
        # Examples of how to check an HttpResponseError
        # Check by error code:
        if error.error is not None:
            if error.error.code == "InvalidImage":
                print(f"Received an invalid image error: {error.error}")
            if error.error.code == "InvalidRequest":
                print(f"Received an invalid request error: {error.error}")
            # Raise the error again after printing it
            raise
        # If the inner error is None and then it is possible to check
        # the message to get more information:
        if "Invalid request".casefold() in error.message.casefold():
            print(f"Uh-oh! Seems there was an invalid request: {error}")
        # Raise the error again
        raise

    logging.info("Done")


def is_pdf(file_name):
    """ Function to check whether a file is a PDF """
    # Get the file extension using os.path.splitext
    file_ext = os.path.splitext(file_name)[1]
    # Return True if the extension is .pdf, False otherwise
    return file_ext == ".pdf"


def sort_key(element):
    """ Function to sort elements by page number and role priority """
    return element["page"]
    # to do, more complex sorting logic to cope with indented bulleted lists
    # return (element["page"], element["role_priority"], element["bounding_region"][0]["x"],
    # element["bounding_region"][0]["y"])


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """ Function to return the number of tokens in a text string"""
    # Returns the number of tokens in a text string
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


class paragraph_roles(Enum):
    """ Enum to define the priority of paragraph roles """
    pageHeader      = 1
    title           = 2
    sectionHeading  = 3
    other           = 3
    footnote        = 5
    pageFooter      = 6
    pageNumber      = 7


def role_prioroty(role):
    """ Function to return the priority of a paragraph role"""
    priority = 0
    match role:
        case "title":
            priority = paragraph_roles.title.value
        case "sectionHeading":
            priority = paragraph_roles.sectionHeading.value
        case "footnote":
            priority = paragraph_roles.footnote.value
        case "pageHeader" :
            priority = paragraph_roles.pageHeader.value            
        case "pageFooter" :
            priority = paragraph_roles.pageFooter.value
        case "pageNumber" :
            priority = paragraph_roles.pageNumber.value     
        case other:     # content
            priority = paragraph_roles.other.value         
    return (priority)


# Load a pre-trained tokenizer
tokenizer = nltk.tokenize.word_tokenize

# Load a set of known English words
word_set = set(nltk.corpus.words.words())


# Define a function to check whether a token is a real English word
def is_real_word(token):
    """ Function to check whether a token is a real English word"""
    return token.lower() in word_set

# Define a function to check whether a string contains real English words
def contains_real_words(string):
    """ Function to check whether a string contains real English words"""
    tokens = tokenizer(string)
    real_word_count = sum(1 for token in tokens if is_real_word(token))
    # Require at least 50% of tokens to be real words and at least one word
    return (real_word_count / len(tokens) > REAL_WORDS_TARGET) and (len(tokens) >= 1)


def format_polygon(polygon):
    """ Function to format a polygon for display"""
    if not polygon:
        return "N/A"
    return ", ".join([f"[{p.x}, {p.y}]" for p in polygon])

def token_count(input_text):
    """ Function to return the number of tokens in a text string"""
    # calc token count
    encoding = "cl100k_base"    # For gpt-4, gpt-3.5-turbo, text-embedding-ada-002, you need to use cl100k_base
    token_count = num_tokens_from_string(input_text, encoding)
    return token_count

def analyze_layout(myblob: func.InputStream):
    """ Function to analyze the layout of a PDF file and extract text using Azure Form Recognizer"""
    if is_pdf(myblob.name):

        logging.info("processing pdf %s", myblob.name)

        azure_blob_storage_account = os.environ["AZURE_BLOB_STORAGE_ACCOUNT"]
        azure_blob_drop_storage_container = os.environ["AZURE_BLOB_DROP_STORAGE_CONTAINER"]
        azure_blob_content_storage_container = os.environ["AZURE_BLOB_CONTENT_STORAGE_CONTAINER"]
        azure_blob_storage_key = os.environ["AZURE_BLOB_STORAGE_KEY"]
        base_filename = os.path.basename(myblob.name)

        # Get path and file name minus the root container
        separator = "/"
        file_path_w_name_no_cont = separator.join(
            myblob.name.split(separator)[1:])

        # Get the folders to use when creating the new files
        folder_set = file_path_w_name_no_cont.removesuffix(
            f'/{base_filename}')

        # Gen SAS token
        sas_token = generate_blob_sas(
            account_name=azure_blob_storage_account,
            container_name=azure_blob_drop_storage_container,
            blob_name=file_path_w_name_no_cont,
            account_key=azure_blob_storage_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        source_blob_path = f'https://{azure_blob_storage_account}.blob.core.windows.net/{myblob.name}?{sas_token}'
        source_blob_path = source_blob_path.replace(" ", "%20")

    # [START extract_layout]
    endpoint = os.environ["AZURE_FORM_RECOGNIZER_ENDPOINT"]
    key = os.environ["AZURE_FORM_RECOGNIZER_KEY"]

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    if TARGET_PAGES == "ALL":
        poller = document_analysis_client.begin_analyze_document_from_url(
            "prebuilt-layout", document_url=source_blob_path
        )
    else :
        poller = document_analysis_client.begin_analyze_document_from_url(
            "prebuilt-layout", document_url=source_blob_path, pages=TARGET_PAGES
        )
    result = poller.result()

    for idx, style in enumerate(result.styles):
        print(
            "Document contains %s content", 
            "handwritten" if style.is_handwritten else "no handwritten"
        )

    for page in result.pages:
        print(f"----Analyzing layout from page #{page.page_number}----")
        print(
            f"Page has width: {page.width} and height: {page.height}, \
                  measured with unit: {page.unit}"
        )

        for line_idx, line in enumerate(page.lines):
            words = line.get_words()
            print(
                "...Line # {} has word count {} and text '{}' within bounding polygon '{}'".format(
                    line_idx,
                    len(words),
                    line.content,
                    format_polygon(line.polygon),
                )
            )

            for word in words:
                print(
                    "......Word '{}' has a confidence of {}".format(
                        word.content, word.confidence
                    )
                )

        for selection_mark in page.selection_marks:
            print(
                "...Selection mark is '{}' within bounding polygon '{}' and has a confidence of {}".format(
                    selection_mark.state,
                    format_polygon(selection_mark.polygon),
                    selection_mark.confidence,
                )
            )

    for table_idx, table in enumerate(result.tables):
        print(
            "Table # {} has {} rows and {} columns".format(
                table_idx, table.row_count, table.column_count
            )
        )
        for region in table.bounding_regions:
            print(
                "Table # {} location on page: {} is {}".format(
                    table_idx,
                    region.page_number,
                    format_polygon(region.polygon),
                )
            )
        for cell in table.cells:
            print(
                "...Cell[{}][{}] has content '{}'".format(
                    cell.row_index,
                    cell.column_index,
                    cell.content,
                )
            )
            for region in cell.bounding_regions:
                print(
                    "...content on page {} is within bounding polygon '{}'".format(
                        region.page_number,
                        format_polygon(region.polygon),
                    )
                )

    # build the json structure
    pargraph_elements = []
    title = ""
    section_heading = ""
    for paragraph in result.paragraphs: 
        # only porcess content, titles and sectionHeading 
        if paragraph.role == "title" or paragraph.role == "sectionHeading" or paragraph.role == None:
            polygon_elements = []
            # store the most recent title and subheading as context data
            if paragraph.role == "title":
                title = paragraph.content   
            if paragraph.role == "sectionHeading":
                section_heading = paragraph.content         
            for point in paragraph.bounding_regions[0].polygon:
                polygon_elements.append({
                    "x": round(point.x, XY_ROUNDING_FACTOR),
                    "y": round(point.y, XY_ROUNDING_FACTOR)
                })
            pargraph_elements.append({
                "page": paragraph.bounding_regions[0].page_number,
                "role_priority": role_prioroty(paragraph.role),
                "role": paragraph.role,
                "bounding_region": polygon_elements,   
                "content": paragraph.content,  
                "title": title,
                "section_heading": section_heading
            })           

    # sort
    pargraph_elements.sort(key=sort_key)

    # extract the content by paragraph with title, sectionHeading & pageHeader and write as a chunk
    blob_service_client = BlobServiceClient(
    f'https://{azure_blob_storage_account}.blob.core.windows.net/', azure_blob_storage_key)
    file_number = 0
    chunk_text = ""
    chunk_size = 0
    paragraph_size = 0
    section_name = ""
    title_name = ""
    target_size_reached = False
    
    for paragraph_element in pargraph_elements:

        if paragraph_element["role"] == None and contains_real_words(paragraph_element["content"]) == True:
            title_name = paragraph_element["title"]
            section_name = paragraph_element["section_heading"]
            # build chunck from paragraphs until target size is reached  
            paragraph_size = token_count(paragraph_element["content"])
            if chunk_size + paragraph_size <= CHUNK_TARGET_SIZE:
                chunk_size = chunk_size + paragraph_size
                chunk_text = chunk_text + "\n" + paragraph_element["content"]
            else:
                # if target chunk size is hit then write out file
                target_size_reached = True 

        if (paragraph_element["role"] != None or target_size_reached == True) and chunk_text != ""  :
            # if its a new section then write out file and if there is text to write
            chunk_output = title_name + "\n" + \
                section_name + "\n\n" + \
                chunk_text       
            output_filename = os.path.splitext(os.path.basename(base_filename))[0] + f"-{file_number}" + ".txt"
            block_blob_client = blob_service_client.get_blob_client(
                container=azure_blob_content_storage_container, blob=f'{folder_set}/{os.path.basename(myblob.name)}/{output_filename}')
            block_blob_client.upload_blob(chunk_output.encode('utf-8'), overwrite=True)

            # reset counters
            file_number += 1            

            # if we wrote the file because we hit the token target, then start with the last paragraph porcessed
            if target_size_reached == True:
                chunk_text = paragraph_element["content"]
                chunk_size = paragraph_size   
                target_size_reached = False 
            else:
                chunk_text = ""
                chunk_size = 0    

    print("done")