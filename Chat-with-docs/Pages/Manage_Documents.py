# Manage-Document Page.
import openai
from anyio import sleep
import streamlit as st
from pydantic import BaseModel # ENSURES INPUT DATA MATCHES THE EXPECTED TYPES.
from db import DocumentInformationChunks, DocumentTags, Tags, db, Documents, set_openai_api_key
from constants import CREATE_FACT_CHUNKS_SYSTEM_PROMPT, GET_MATCHING_TAGS_SYSTEM_PROMPT

from utils import find

# FUNCTION TO DELETE DOCUMENT FROM DATABSE.
def delete_document(document_id: int):
    Documents.delete().where(Documents.id == document_id).execute()
    
# BUILD USER-INTERFACE USING STREAMLIT.
st.set_page_config(page_title = "Manage Documents")
st.title("Manage Documents")

IDEAL_CHUNK_LENGTH = 4000

# 1. DIVIDE THE DOCUMENTS INTO CHUNKS AND EXTRACT FACTS(FACTUAL INFORMATION) OUT OF IT.

# CLASS DEFINED USING 'pydantic' LIBRARY, COMMANLY USED FOR DATA-VALIDATION AND PARSING.
class GeneratedDocumentInformationChunks(BaseModel): 
    facts: list[str]

# ASYNC-FUNCTION: CAN PAUSE AT CERTAIN POINTS(WAITING FOR SOMETHING TO FINISH) AND LET OTHER WORK HAPPEN IN THE MEANTIME.    
# USED TO LOAD DOCUMENTS, MAKING HTTPS REQUESTS(READING DATA FROM INTERNET).

# FUNCTION THAT GENERATES CHUNK/FACTS(FOCUED ON KEY-INFORMATION/FACTS) FROM DOCUMENT-CHUNK.
async def generate_chunks(index: int, pdf_text_chunk: str):
    # REQUEST OPENAI ATLEAST 5 TIMES TO GENERATE CHUNKS(FOCUDES ON KEY-INFORMATION).
    count_request = 0
    # TRY SENDING REQUEST TO GPT, IF IT FAILS(ERROR) ----> TRY ATLEAST 5 TIMES WITH 2SEC AWAIT.
    while(True):
        try:
            # INTERACT WITH OPENAI API.
            output = await openai.ChatCompletion.acreate(
                model = 'gpt-4o-mini-2024-07-18',
                messages = [{'role': 'system', 'content': CREATE_FACT_CHUNKS_SYSTEM_PROMPT},
                            {'role': 'user', 'content': pdf_text_chunk}],
                temperature = 0.1, # LESS RANDOMNESS(SAFE ANSWER)
                top_p = 1,
                frequency_penalty = 0,
                presence_penalty = 0,
                response_format = {
                    "type": "json_object"
                }
            )
            
            # IF FACTS ARE NOT GENERATED.
            if not output.choices[0].message.content:
                raise Exception('No facts generated')
            
            # VALIDATE AND EXTRACT THE FACTS AS A STRING(FROM JSON FORMATE) FROM GENERATED OUTPUT.
            document_information_chunks = GeneratedDocumentInformationChunks.model_validate_json(output.choices[0].message.content).facts
            # ".model_validate_json()" PARSES THE OUTPUT(JSON) AND CONVERTS IT AS ATTRIBUTE DEFINED IN 'GeneratedDocumentInformationChunks' CLASS.
            # EG: {'FACTS': [FACT-1, FACT-2, FACT-3]} --------> FACTS = [FACT-1, FACT-2, FACT-3]
            print(f"Generated {len(document_information_chunks)} facts for pdf text chunk {index}.")

            return document_information_chunks
        except Exception as e:
            count_request += 1 
            
            if count_request > 5:
                raise e # AFTER 5 REQUESTS, RAISE ERROR.
            
            await  sleep(2) # AWAIT 2SEC - BEFORE SENDING OTHER REQUEST. BECAUSE SOMETIMES REQUESTS FAILS.
            print(f"Failed to generate facts for pdf text chunk {index} with this err: {e}. Retrying...")

# 2. MATCH THE TAG FOR DOCUMENT(TO ASSIGN A TAG FOR A DOCUMENT).

class GeneratedMatchingTags(BaseModel): # FOR VALIDATING AND PARSING THE DATA.
    tags: list[str]
    
async def get_matching_tags(pdf_text: str):
    tags_result = Tags.select() # EXTRACT ALL THE TAGS FROM 'TAGS-TABLE' IN DATABASE.
    tags = [tag.lower() for tag in tags_result] 
    
    # IF THERE ARE NO TAGS IN 'TAGS-TABLE' IN DATABASE
    if not len(tags):
        return []
    
    # USE LLM(MODLES) TO MATCH THE TAGS FOR DOCUMENT BASED ON CONENT OF A DOCUMENT.
    count_requests = 0
    while True:
        try:
            # INTERACT WITH OPENAI API TO MATCH THE TAG.
            output = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "system",
                        "content": GET_MATCHING_TAGS_SYSTEM_PROMPT.replace("{{tags_to_match_with}}", str(tags))
                    },
                    {
                        "role": "user",
                        "content": pdf_text
                    }
                ],
                temperature=0.1,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={
                    "type": "json_object"
                }
            )
            
            # IF RESPONSE HAS NOT GENERATED. 
            if not output.choices[0].message.content:
                raise Exception("Empty response for generating matching tags.")
            
            # VALIDATE, PARSE AND EXTRACT THE MATRCHING-TAG.
            matching_tag_names = GeneratedMatchingTags.model_validate_json(output.choices[0].message.content).tags
            
            # EXTRACT THE ID(OF TAG) - GET MATCHING-TAG ID.
            matching_tag_ids: list[int] = []
            for tag_name in matching_tag_names:
                matching_tag = find(lambda tag: tag.name.lower() == tag_name.lower(), tags_result)
                if matching_tag:
                    matching_tag_ids.append(matching_tag.id)
        except Exception as e:
            # TRY REQUESTING OPENAI API FOR 5 TIMES, INCASE SOME ERROR OCCURED WHILE INTERACTING WITH OPENAI API. 
            count_requests += 1
            if count_requests > 5:
                raise e
            
            await sleep(2) # 2sec delay for next request.   
    
    