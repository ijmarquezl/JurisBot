import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables to ensure MONGO_URI is available
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "jurisconsultor") # Default to 'jurisconsultor'
MONGO_MEMORY_DB_NAME = os.getenv("MONGO_MEMORY_DB_NAME", "jurisconsultor_memory") # Default to 'jurisconsultor_memory'

if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable not set.")

# Create a single, reusable client instance
client = MongoClient(MONGO_URI)

def get_db():
    """Returns the main application database from the client."""
    return client[MONGO_DB_NAME]

def get_memory_db():
    """Returns the database specifically for the agent's memory."""
    return client[MONGO_MEMORY_DB_NAME]

def close_db_connection():
    """Closes the client's connection to MongoDB."""
    client.close()
