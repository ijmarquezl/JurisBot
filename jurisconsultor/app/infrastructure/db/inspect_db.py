from infrastructure.utils.utils import get_mongo_client
import os
from bson import ObjectId

db_name = os.getenv('MONGO_DB_NAME', 'jurisconsultor')
client = get_mongo_client()
db = client[db_name]

print(f'DB: {db_name}')
target_id = "6933882f63fef5c842516969"

try:
    oid = ObjectId(target_id)
    company = db.companies.find_one({"_id": oid})
    print(f"Company found by ObjectId: {company}")
except:
    pass

company_str = db.companies.find_one({"_id": target_id})
print(f"Company found by String ID: {company_str}")

all_companies = list(db.companies.find({}))
print(f"All Companies: {all_companies}")
