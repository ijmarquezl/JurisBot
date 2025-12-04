import os
import re
import requests
import json
import logging
from typing import List, Dict, Any # New import
from functools import lru_cache
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_values
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
from tenacity import retry, wait_fixed, stop_after_attempt, before_log, after_log, retry_if_exception_type

# Setup logger for this module
logger = logging.getLogger(__name__)

# --- Database and Model Caching ---

@retry(
    wait=wait_fixed(2),
    stop=stop_after_attempt(5),
    reraise=True,
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO),
    retry=(
        retry_if_exception_type(ConnectionFailure) |
        retry_if_exception_type(ServerSelectionTimeoutError)
    )
)
@lru_cache(maxsize=1)
def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set.")
    logger.info("Attempting to connect to MongoDB...")
    client = MongoClient(mongo_uri)
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
    logger.info("MongoDB connection successful.")
    return client

@lru_cache(maxsize=1)
def get_embedding_model():
    model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    return SentenceTransformer(model_name)

def get_public_db_conn():
    public_postgres_uri = os.getenv("PUBLIC_POSTGRES_URI")
    if not public_postgres_uri:
        raise ValueError("PUBLIC_POSTGRES_URI environment variable not set.")
    return psycopg2.connect(public_postgres_uri)

def get_private_db_conn():
    private_postgres_uri = os.getenv("PRIVATE_POSTGRES_URI")
    if not private_postgres_uri:
        raise ValueError("PRIVATE_POSTGRES_URI environment variable not set.")
    return psycopg2.connect(private_postgres_uri)

# --- Embedding Generation ---

def generate_embedding(text: str):
    model = get_embedding_model()
    return model.encode(text)

# --- LLM & RAG Core Logic ---

LLM_URL = os.getenv("LLM_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_llm(prompt: str, json_format: bool = False) -> str:
    """Generic function to call the LLM (Groq compatible)."""
    if not LLM_URL or not GROQ_API_KEY:
        raise ValueError("LLM_URL and GROQ_API_KEY environment variables must be set.")
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        payload = {
            "messages": messages,
            "model": os.getenv("LLM_MODEL_NAME", "llama3-8b-8192"), # Default Groq model, can be made configurable
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False
        }
        
        if json_format:
            payload["response_format"] = {"type": "json_object"}

        # Ensure the URL has the correct endpoint
        full_url = LLM_URL.rstrip('/') + "/chat/completions"

        response = requests.post(full_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while querying the LLM: {e}")
        return f"Error: No se pudo obtener una respuesta del modelo de lenguaje. {e}"

def find_relevant_documents(query_embedding, top_k=3, query_text: str = None):
    """
    Finds the most relevant document chunks from the database using a hybrid approach
    (vector search + keyword search).
    """
    try:
        conn = get_public_db_conn()
        cur = conn.cursor()
        
        # 1. Vector Search
        embedding_str = str(query_embedding.tolist())
        sql_query = "SELECT content, source FROM documents ORDER BY embedding <-> %s LIMIT %s;"
        logger.info(f"Executing RAG retrieval (vector) query with limit {top_k}")
        cur.execute(sql_query, (embedding_str, top_k))
        vector_results = cur.fetchall()
        
        # 2. Keyword Search
        keyword_results = []
        if query_text:
            logger.info(f"Executing RAG retrieval (keyword) for: {query_text}")
            # The query_text now contains keywords separated by spaces.
            # We will format them for a ts_query with an OR operator.
            keyword_query = " | ".join(query_text.split())
            
            # Use ts_query for full-text search
            sql_keyword_query = "SELECT content, source FROM documents, to_tsvector('spanish', content) document_vectors, to_tsquery('spanish', %s) query WHERE query @@ document_vectors LIMIT %s;"
            try:
                cur.execute(sql_keyword_query, (keyword_query, top_k))
                keyword_results = cur.fetchall()
            except Exception as ts_e:
                logger.error(f"Full-text search failed: {ts_e}. Falling back to LIKE.")
                # Fallback to LIKE if full-text search is not available or fails
                sql_like_query = "SELECT content, source FROM documents WHERE content ILIKE %s LIMIT %s;"
                cur.execute(sql_like_query, (f'%{query_text.replace(" ", "%")}%', top_k))
                keyword_results = cur.fetchall()


        # 3. Combine and de-duplicate results
        combined_results = {res: True for res in vector_results}
        for res in keyword_results:
            combined_results[res] = True
            
        final_results = list(combined_results.keys())
        
        cur.close()
        conn.close()
        logger.info(f"RAG retrieval results (hybrid): {final_results}")
        return final_results
    except Exception as e:
        logger.error(f"An error occurred during document retrieval: {e}")
        return []

def answer_with_rag(question: str) -> str:
    """Answers a question using the RAG pipeline with HyDE and keyword extraction."""
    logger.info(f"---Invoking RAG for: {question}---")
    try:
        # 1. Generate a hypothetical document (HyDE) for vector search
        hyde_prompt = f"""Por favor, escribe un fragmento de un documento legal que responda a la siguiente pregunta. No es necesario que sea legalmente preciso, solo que contenga el tipo de lenguaje y terminología que se encontraría en un texto legal real.
        Pregunta: {question}
        Documento Hipotético:"""
        hypothetical_document = call_llm(hyde_prompt)
        logger.debug(f"Generated hypothetical document for HyDE: {hypothetical_document}")
        question_embedding = generate_embedding(hypothetical_document)

        # 2. Extract keywords for full-text search
        keyword_prompt = f"""Extrae las 3-5 palabras clave más importantes de la siguiente pregunta para una búsqueda en una base de datos legal. Devuelve solo las palabras clave separadas por espacios.
        Pregunta: {question}
        Palabras Clave:"""
        keywords = call_llm(keyword_prompt)
        logger.info(f"Extracted keywords for search: {keywords}")

        # 3. Find relevant documents using the hybrid approach
        relevant_docs = find_relevant_documents(question_embedding, query_text=keywords)
        if not relevant_docs:
            logger.warning("No relevant documents found for RAG.")
            return "Error: No se encontraron documentos relevantes para responder a la pregunta del usuario."
        
        # 4. Generate the final answer using the retrieved context
        context = "\n".join([f'Fuente: {source}\nContenido: {content}' for content, source in relevant_docs])
        logger.info(f"Context passed to LLM for RAG: {context}")
        
        rag_prompt_template = """Eres un asistente legal experto. Tu tarea es responder a la pregunta del usuario basándote ESTRICTAMENTE y ÚNICAMENTE en el contexto proporcionado. Si la respuesta no se encuentra explícitamente en el contexto, DEBES indicar claramente que no tienes información al respecto y BAJO NINGUNA CIRCUNSTANCIA DEBES sugerir artículos o leyes que no estén en el contexto. NO ALUCINES.
        Tu respuesta debe ser concisa, directa y en ESPAÑOL. Si se te pide una lista de artículos o leyes, proporciona solo los que estén explícitamente mencionados en el contexto y sean relevantes para la pregunta.

        Contexto:
        {context}

        Pregunta: {question}

        Respuesta:"""
        
        prompt = rag_prompt_template.format(context=context, question=question)
        
        return call_llm(prompt)
    except Exception as e:
        logger.error(f"Error executing RAG search: {e}")
        return f"Error executing RAG search: {e}"

def search_raw_documents(query: str) -> List[Dict[str, Any]]:
    """Searches raw document content in PostgreSQL for a given query string."""
    try:
        conn = get_public_db_conn()
        cur = conn.cursor()
        # Using ILIKE for case-insensitive search
        sql_query = "SELECT content, source FROM documents WHERE content ILIKE %s LIMIT 10;"
        logger.info(f"Executing raw document search query: {sql_query} with query: {query}")
        cur.execute(sql_query, (f'%{query}%',))
        results = cur.fetchall()
        cur.close()
        conn.close()
        logger.info(f"Raw document search results: {results}")
        return [{'content': r[0], 'source': r[1]} for r in results]
    except Exception as e:
        logger.error(f"Error searching raw documents: {e}")
        return []