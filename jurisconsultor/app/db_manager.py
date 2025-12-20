import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "jurisconsultor") # Default to 'jurisconsultor'
MONGO_MEMORY_DB_NAME = os.getenv("MONGO_MEMORY_DB_NAME", "jurisconsultor_memory") # Default to 'jurisconsultor_memory'

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable not set.")

from functools import lru_cache

# Create a single, reusable client instance for main DB
client = MongoClient(MONGO_URI)

def get_db():
    """Returns the main application database from the client."""
    return client[MONGO_DB_NAME]

def get_memory_db():
    """Returns the database specifically for the agent's memory."""
    return client[MONGO_MEMORY_DB_NAME]

@lru_cache(maxsize=100)
def get_tenant_client(mongo_uri: str):
    """Cached client for tenant databases."""
    return MongoClient(mongo_uri)

def get_tenant_db(mongo_uri: str, db_name: str):
    """Returns a tenant-specific database connection."""
    client = get_tenant_client(mongo_uri)
    return client[db_name]

def close_db_connection():
    """Closes the client's connection to MongoDB."""
    client.close()

def log_llm_usage(tenant_id: str, user_email: str, model: str, input_tokens: int, output_tokens: int, cost: float = 0.0):
    """
    Logs LLM usage to the main database.
    This is used for billing and monitoring purposes.
    """
    try:
        db = get_db()
        from datetime import datetime
        usage_record = {
            "timestamp": datetime.utcnow(),
            "tenant_id": tenant_id,
            "user_email": user_email,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost
        }
        db.llm_usage.insert_one(usage_record)
    except Exception as e:
        # We don't want to crash the request if logging fails, but we should log the error
        import logging
        logging.getLogger(__name__).error(f"Failed to log LLM usage: {e}")
