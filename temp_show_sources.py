import os
from pymongo import MongoClient
from pprint import pprint

def show_sources():
    """
    Connects to the database and lists all documents in the 'scraping_sources'
    collection to verify its contents.
    """
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME", "jurisconsultor")
    
    if not mongo_uri:
        print("Error: MONGO_URI not found in environment variables.")
        return

    client = None
    try:
        print(f"Connecting to MongoDB...")
        client = MongoClient(mongo_uri)
        db = client[db_name]
        sources_collection = db["scraping_sources"]
        
        print(f"Querying collection 'scraping_sources' in database '{db_name}'...")
        
        count = sources_collection.count_documents({})
        print(f"Found {count} documents in total.")
        
        all_sources = list(sources_collection.find({}))
        
        if not all_sources:
            print("The 'scraping_sources' collection is empty.")
        else:
            print("--- Contents of 'scraping_sources' collection ---")
            for source in all_sources:
                pprint(source)
                print("---")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if client:
            client.close()
            print("MongoDB connection closed.")

if __name__ == "__main__":
    show_sources()
