from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory  # Memory to store and manage conversation
from langchain.chains import ConversationalRetrievalChain
from langchain_groq import ChatGroq
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# Load PDFs
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()  # Append extracted text
    return text

# Tokenize the raw text into chunks
def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(separator='\n', chunk_size=1000, chunk_overlap=200, length_function=len)
    chunks = text_splitter.split_text(raw_text)
    return chunks

# Create vector store from text chunks
def get_vector_store(text_chunks):
    embeddings = OllamaEmbeddings()
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vector_store

# Build Streamlit Interface
st.set_page_config(page_title='PDF Querying', page_icon='📄')

st.header('Query From Multiple PDFs')
query = st.text_input('Ask GPT')

# Sidebar for file upload
with st.sidebar:
    st.subheader('Your Documents')
    pdf_docs = st.file_uploader('Upload PDF', accept_multiple_files=True)
    
    # Process PDFs and create embeddings when the 'Process' button is pressed
    if st.button('Process'):
        with st.spinner('Processing...'):
            if pdf_docs:
                # 1. Load PDFs
                raw_text = get_pdf_text(pdf_docs)
                
                # 2. Tokenization into chunks
                text_chunks = get_text_chunks(raw_text)
                
                # 3. Create the vector store
                vector_store = get_vector_store(text_chunks)
                
                # Notify user
                st.write('Text Processed')
                
                # Initialize the LLM model
                llm = ChatGroq(
                    groq_api_key=os.getenv('GROQ_API_KEY'),
                    model="llama-3.1-70b-versatile",
                    temperature=0,
                )
                
                # Create memory for the conversation
                memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
                
                # Initialize the ConversationalRetrievalChain with the vector store and memory
                if 'conversation' not in st.session_state:
                    st.session_state.conversation = ConversationalRetrievalChain.from_llm(
                        llm, vector_store.as_retriever(), memory=memory
                    )
                
                st.write("Ready for queries!")

# Handle user query and display response
if query:
    with st.spinner('Processing query...'):
        response = st.session_state.conversation.run(query)
        st.write(response)
