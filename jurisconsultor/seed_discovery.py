import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_discovery_sources():
    """
    Seeds the MongoDB 'scraping_sources' collection with initial discovery URLs.
    """
    load_dotenv()

    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME", "jurisconsultor")

    if not mongo_uri:
        logger.error("MONGO_URI environment variable not set.")
        return

    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db["scraping_sources"]

        # Initial seed data
        seed_entry = {
            "name": "Orden Jurídico Nacional - Leyes",
            "url": "https://www.ordenjuridico.gob.mx/leyes.php",
            "scraper_type": "discovery_ordenjuridico",
            "status": "active",
            "description": "Main index page for Federal and State laws."
        }

        # Upsert: Update if exists, Insert if not
        result = collection.update_one(
            {"url": seed_entry["url"]},
            {"$set": seed_entry},
            upsert=True
        )

        if result.upserted_id:
            logger.info(f"Inserted new discovery source: {seed_entry['name']}")
        elif result.modified_count > 0:
            logger.info(f"Updated existing discovery source: {seed_entry['name']}")
        else:
            logger.info(f"Discovery source already exists and is up to date: {seed_entry['name']}")

    except Exception as e:
        logger.error(f"Failed to seed discovery sources: {e}", exc_info=True)

if __name__ == "__main__":
    seed_discovery_sources()
