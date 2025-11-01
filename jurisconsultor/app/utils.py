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
from dotenv import load_dotenv

# Setup logger for this module
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Database and Model Caching ---

@lru_cache(maxsize=1)
def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set.")
    return MongoClient(mongo_uri)

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

def call_llm(prompt: str, json_format: bool = False) -> str:
    """Generic function to call the LLM."""
    if not LLM_URL:
        raise ValueError("LLM_URL environment variable not set.")
    try:
        payload = {"model": "llama3", "prompt": prompt, "stream": False}
        if json_format:
            payload["format"] = "json"
        response = requests.post(f"{LLM_URL}/api/generate", json=payload)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while querying the LLM: {e}")
        return f"Error: No se pudo obtener una respuesta del modelo de lenguaje. {e}"

def find_relevant_documents(query_embedding, top_k=5, query_text: str = None):
    """Finds the most relevant document chunks from the database, with a keyword fallback."""
    try:
        conn = get_public_db_conn()
        cur = conn.cursor()
        embedding_str = str(query_embedding.tolist())
        
        sql_query = "SELECT content, source FROM documents ORDER BY embedding <-> %s LIMIT %s;"
        logger.info(f"Executing RAG retrieval (vector) query: {sql_query} with embedding (first 10 elements): {embedding_str[:100]}... and limit {top_k}")
        
        cur.execute(sql_query, (embedding_str, top_k))
        results = cur.fetchall()
        
        if not results and query_text: # Fallback to keyword search if vector search yields nothing
            logger.info(f"Vector search returned no results. Falling back to keyword search for: {query_text}")
            keyword_results = search_raw_documents(query_text)
            # Filter keyword results to only include content and source
            results = [(r['content'], r['source']) for r in keyword_results]
            
        cur.close()
        conn.close()
        logger.info(f"RAG retrieval results: {results}")
        return results
    except Exception as e:
        logger.error(f"An error occurred during document retrieval: {e}")
        return []

def answer_with_rag(question: str) -> str:
    """Answers a question using the RAG pipeline."""
    logger.info(f"---Invoking RAG for: {question}---")
    try:
        # Extract just the facts for embedding
        facts_match = re.search(r"Based on the following facts: (.*?), what legal articles", question)
        facts_only_query = facts_match.group(1) if facts_match else question

        question_embedding = generate_embedding(facts_only_query)
        
        # Pass the facts_only_query as query_text for fallback
        relevant_docs = find_relevant_documents(question_embedding, query_text=facts_only_query)
        if not relevant_docs:
            logger.info("No relevant documents found for RAG.")
            return "No se encontraron documentos relevantes para responder a su pregunta."
        
        context = "\n".join([f'Fuente: {source}\nContenido: {content}' for content, source in relevant_docs])
        logger.info(f"Context passed to LLM for RAG: {context}")
        
        # Refined prompt for better RAG quality and Spanish output
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