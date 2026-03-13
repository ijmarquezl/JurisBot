import os
import secrets
import string
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from slugify import slugify
from pymongo import MongoClient

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

app = FastAPI(title="JurisBot Infrastructure Orchestrator")

# SHARED MONGO CONFIG
# Get URI from environment options
SHARED_MONGO_URI = os.getenv("MONGO_SHARED_URI")
if not SHARED_MONGO_URI:
    # Fallback/Default for dev
    SHARED_MONGO_USER = os.getenv("MONGO_SHARED_ROOT_USERNAME", "root")
    SHARED_MONGO_PASS = os.getenv("MONGO_SHARED_ROOT_PASSWORD", "secure_root_password")
    SHARED_MONGO_URI = f"mongodb://{SHARED_MONGO_USER}:{SHARED_MONGO_PASS}@mongodb_shared:27017/?authSource=admin"

logger.info(f"Orchestrator configured with Shared Mongo: {SHARED_MONGO_URI}")

class TenantRequest(BaseModel):
    company_id: str
    company_name: str

class ProvisioningResponse(BaseModel):
    message: str
    mongo_uri: str
    mongo_db_name: str

def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def get_shared_client():
    return MongoClient(SHARED_MONGO_URI)

@app.post("/provision-tenant", response_model=ProvisioningResponse)
async def provision_tenant(request: TenantRequest):
    """
    Provisions a new isolated Database and User in the Shared MongoDB Cluster.
    No new containers are created.
    """
    tenant_slug = slugify(request.company_name)
    company_id = request.company_id
    
    # 1. Define Names
    db_name = f"db_{tenant_slug}_{company_id}"
    db_user = f"user_{company_id}"
    db_password = generate_password()

    logger.info(f"Provisioning tenant for {request.company_name} (DB: {db_name})...")

    try:
        # 2. Connect to Shared Mongo as Admin
        client = get_shared_client()
        target_db = client[db_name]

        # 3. Create User with 'dbOwner' role for this specific DB
        # The 'createUser' command is idempotent-ish (fails if exists), so we handle that.
        
        try:
            target_db.command(
                "createUser", 
                db_user, 
                pwd=db_password, 
                roles=[{"role": "dbOwner", "db": db_name}]
            )
            logger.info(f"User {db_user} created for DB {db_name}.")
            message = "Tenant database provisioned successfully."
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"User {db_user} already exists. Updating password.")
                target_db.command("updateUser", db_user, pwd=db_password)
                message = "Tenant database existence confirmed. Password rotated."
            else:
                raise e

        # 4. Construct Connection URI
        # The connection string for the tenant MUST point to the shared host
        # but authenticate as the tenant user against the tenant DB.
        mongo_uri = f"mongodb://{db_user}:{db_password}@mongodb_shared:27017/{db_name}?authSource={db_name}"

        return ProvisioningResponse(
            message=message,
            mongo_uri=mongo_uri,
            mongo_db_name=db_name
        )

    except Exception as e:
        logger.error(f"Failed to provision database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to provision database: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "ok", "backend": "shared_mongo_cluster"}
