import logging
import sys
# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from routers.superadmin import create_company
from models import CompanyCreate
from db_manager import get_db

logger = logging.getLogger("validation")

def test_provisioning():
    db = get_db()
    
    # Clean up previous test if exists
    existing = db.companies.find_one({"name": "Dynamic Test Company"})
    if existing:
        logger.info("Cleaning up previous test company...")
        db.companies.delete_one({"_id": existing["_id"]})
        
    logger.info("Creating new company...")
    try:
        new_company = CompanyCreate(name="Dynamic Test Company")
        result = create_company(new_company, db)
        
        logger.info(f"Company created: {result.name}")
        logger.info(f"ID: {result.id}")
        logger.info(f"Infra Status: {result.infrastructure_status}")
        logger.info(f"Mongo URI: {result.mongo_uri}")
        
        if result.infrastructure_status != "provisioned":
             logger.error("Provisioning failed!")
             sys.exit(1)
        
        if not result.mongo_uri:
             logger.error("No Mongo URI returned!")
             sys.exit(1)
             
        logger.info("SUCCESS: Infrastructure provisioned.")
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        # Print full stack trace
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_provisioning()
