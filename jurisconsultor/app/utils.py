
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

def get_postgres_conn():
    """
    Returns a PostgreSQL connection object.
    """
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        raise ValueError("POSTGRES_URI environment variable not set.")
    return psycopg2.connect(postgres_uri)

def generate_embedding(text):
    """
    Generates an embedding for the given text.
    """
    if embedding_model:
        return embedding_model.encode(text)
    else:
        raise ValueError("Embedding model not loaded.")
