
import os
import psycopg2
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Initialize the embedding model
embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
if embedding_model_name:
    print(f"Loading embedding model: {embedding_model_name}")
    embedding_model = SentenceTransformer(embedding_model_name)
else:
    print("EMBEDDING_MODEL_NAME environment variable not set.")
    embedding_model = None

def get_mongo_client():
    """
    Returns a MongoClient object.
    """
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set.")
    return MongoClient(mongo_uri)

def get_private_db_conn():
    """
    Returns a connection to the private PostgreSQL database.
    """
    postgres_uri = os.getenv("PRIVATE_POSTGRES_URI")
    if not postgres_uri:
        raise ValueError("PRIVATE_POSTGRES_URI environment variable not set.")
    return psycopg2.connect(postgres_uri)

def get_public_db_conn():
    """
    Returns a connection to the public PostgreSQL database.
    """
    postgres_uri = os.getenv("PUBLIC_POSTGRES_URI")
    if not postgres_uri:
        raise ValueError("PUBLIC_POSTGRES_URI environment variable not set.")
    return psycopg2.connect(postgres_uri)

def generate_embedding(text):
    """
    Generates an embedding for the given text.
    """
    if embedding_model:
        return embedding_model.encode(text)
    else:
        raise ValueError("Embedding model not loaded.")
