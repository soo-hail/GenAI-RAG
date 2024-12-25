import os
import streamlit as st
import psycopg2
from psycopg2.extensions import register_adapter, AsIs
from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load Environment Variables from .env file
load_dotenv()

# PostgreSQL Connection
conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB_NAME'),
    user=os.getenv('POSTGRES_DB_USER'),
    password=os.getenv('POSTGRES_DB_PASSWORD'),
    host=os.getenv('POSTGRES_DB_HOST'),
    port=os.getenv('POSTGRES_DB_PORT')
)
cursor = conn.cursor()  # Helps to execute commands.

# Sample Text Chunks
text_chunks = [
    'AI enables machines to think and act like humans, powering tools like chatbots and self-driving cars.',
    'ML lets systems learn from data to make predictions, like in spam filters and face recognition.',
    'NLP helps computers understand and use human language, seen in translators and voice assistants.'
]

# Build Interface
st.title('Q&A System')
st.write('This application demonstrates the steps in the Q&A pipeline')

# STEP-1: DOCUMENT CHUNKING
st.header('Step-1: Document Chunking')
st.write('Here are the document chunks:')
for i, chunk in enumerate(text_chunks, start=1):
    st.write(f'**Chunk-{i}:** {chunk}')

# STEP-2: Embeddings
st.header('Step-2: Generating Embeddings')
st.write('Each document chunk is converted into vector embeddings')

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
embedding_vectors = [embedding_model.encode(chunk) for chunk in text_chunks]

# Create PostgreSQL Table
cursor.execute("""
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        embeddings VECTOR(384)  -- Match the dimension of your embeddings
    );
""")

# Insert Data into PostgreSQL
for chunk, embedding in zip(text_chunks, embedding_vectors):
    cursor.execute(
        '''
        INSERT INTO document_chunks (content, embeddings) VALUES (%s, %s)
        ''',
        (chunk, embedding.tolist())  # Convert embedding to a list
    )
    
    st.write(f'Embedding for chunk `{chunk}`: ')
    st.write(embedding.tolist())

conn.commit()

# STEP-3: RETRIVE RELAVENT CHUNKS FOR A QUESTION.
st.header('Step-3: Retrive Relevant Chunks')
query = st.text_input('Query about document: ')

def get_relevant_chunks(query, top_n=1):
    try:
        # Generate embeddings for the query
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embeddings = embedding_model.encode(query).tolist()
        
        # Query the database for the most similar chunks
        cursor.execute(
            """
            SELECT content
            FROM document_chunks
            ORDER BY embeddings <=> %s::vector
            LIMIT %s
            """,
            (query_embeddings, top_n)
        )
        
        # Fetch and return the results
        relevant_chunks = [row[0] for row in cursor.fetchall()]
        return relevant_chunks
    
    except Exception as e:
        print(f"Error retrieving relevant chunks: {e}")
        return []
    
if query:
    st.write(f'**Embedding for the question** `{query}`: ')
    # Print Question(Query)-Embedding.
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embeddings = embedding_model.encode(query).tolist()
    st.write(query_embeddings)
    
    relevant_chunks = get_relevant_chunks(query= query)
    for i, chunk in enumerate(relevant_chunks, start = 1):
        st.write(f'{i}. {chunk}')
        
# STEP-4: GENERATE AND DISPLAY THE ANSWER.
st.header('Step-4: Generate Answer using LLAMA3')
    
llm = ChatGroq(
        groq_api_key=os.getenv('GROQ_API_KEY'),
        model="llama-3.1-70b-versatile",
        temperature=0,
    )

if query and relevant_chunks:
    context = ' '.join(relevant_chunks)
    prompt = f"Use the context below to answer the query:\n\nContext: {context}\n\nQuery: {query}\n\nAnswer:"
    try:
        answer = llm.generate([prompt])
        st.write("**Generated Answer:**", answer[0]['text'])
    except Exception as e:
        st.error(f"Error generating answer: {e}")

cursor.close()
conn.close()
