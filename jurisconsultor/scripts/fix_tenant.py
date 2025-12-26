from infrastructure.utils.utils import get_mongo_client
import os
from bson import ObjectId

# 1. Construct URI from env vars present in backend container
user = os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_USER")
password = os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_PASSWORD")
db_name = os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_DB")

if not all([user, password, db_name]):
    print("ERROR: Missing env vars for Mi Primera Empresa")
    exit(1)

# Note: In docker network, host is 'mongodb_mi_primera_empresa'
uri = f"mongodb://{user}:{password}@mongodb_mi_primera_empresa:27017/{db_name}?authSource=admin"

print(f"Constructed URI: {uri}")

# 2. Connect to Public DB and Update
client = get_mongo_client() # Connects to public DB by default
db = client[os.getenv('MONGO_DB_NAME', 'jurisconsultor')]

target_id = "6933882f63fef5c842516969"
try:
    oid = ObjectId(target_id)
    result = db.companies.update_one(
        {"_id": oid},
        {"$set": {
            "mongo_uri": uri,
            "mongo_db_name": db_name,
            "infrastructure_status": "legacy_provisioned"
        }}
    )
    print(f"Update Result (ObjectId): matched={result.matched_count}, modified={result.modified_count}")
except Exception as e:
    print(f"Error updating with ObjectId: {e}")

# Fallback try string ID just in case
if result.matched_count == 0:
    result = db.companies.update_one(
        {"_id": target_id},
        {"$set": {
            "mongo_uri": uri,
            "mongo_db_name": db_name,
             "infrastructure_status": "legacy_provisioned"
        }}
    )
    print(f"Update Result (String): matched={result.matched_count}, modified={result.modified_count}")
