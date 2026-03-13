
import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("switchover")

load_dotenv()

# We are updating the 'companies' collection in the "Main" DB.
# In this architecture, the Main DB was 'mi_primera_empresa_db', which is now on Shared Mongo.
# We need to connect to it using the NEW credentials/URI for shared mongo.

# SHARED CONFIG (Root auth or specific Owner auth)
SHARED_MONGO_HOST = "mongodb_shared"
SHARED_MONGO_PORT = 27017
# Use Root to have access to everything easier for this admin script
SHARED_MONGO_USER = os.getenv("MONGO_SHARED_ROOT_USERNAME", "root")
SHARED_MONGO_PASS = os.getenv("MONGO_SHARED_ROOT_PASSWORD", "secure_root_password")
SHARED_URI = f"mongodb://{SHARED_MONGO_USER}:{SHARED_MONGO_PASS}@127.0.0.1:{SHARED_MONGO_PORT}/?authSource=admin"

# Note: We use 127.0.0.1 assuming we run this via SSH tunnel or if port is mapped. 
# Since we are running from host where port 27017 isn't mapped by default in compose,
# we should probably run this INSIDE the container or map the port temporarily.
# OR, use 'docker exec' with pymongo inside? No, complex.
# EASIEST: Use 'docker exec' + mongosh scripts.

# python script that generates Javascript for mongosh is safer/easier than dependency hell again.

def generate_update_script():
    js_commands = []
    
    # 1. Update Mi Primera Empresa (The Host Tenant)
    db_name_main = os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_DB")
    user_new_main = f"user_{db_name_main}"
    # The URI used BY the backend to connect to this tenant specifically
    uri_main = f"mongodb://{user_new_main}:{os.getenv('TENANT_MI_PRIMERA_EMPRESA_MONGO_PASSWORD')}@mongodb_shared:27017/{db_name_main}?authSource={db_name_main}"
    
    # Find Query: name string or just update all documents? 
    # Logic: Update document where 'name' matches or 'mongo_db_name' matches.
    
    js_commands.append(f"// Update Mi Primera Empresa")
    js_commands.append(f"db.getSiblingDB('{db_name_main}').companies.updateMany({{ 'mongo_db_name': '{db_name_main}' }}, {{ $set: {{ 'mongo_uri': '{uri_main}', 'infrastructure_status': 'migrated_shared' }} }});")

    # 2. Update Tenant A
    db_name_a = os.getenv("TENANT_A_MONGO_DB")
    user_new_a = f"user_{db_name_a}"
    uri_a = f"mongodb://{user_new_a}:{os.getenv('TENANT_A_MONGO_PASSWORD')}@mongodb_shared:27017/{db_name_a}?authSource={db_name_a}"
    
    js_commands.append(f"// Update Tenant A")
    js_commands.append(f"db.getSiblingDB('{db_name_main}').companies.updateMany({{ 'mongo_db_name': '{db_name_a}' }}, {{ $set: {{ 'mongo_uri': '{uri_a}', 'infrastructure_status': 'migrated_shared' }} }});")

    return "\n".join(js_commands)

if __name__ == "__main__":
    script_content = generate_update_script()
    print("Generated Mongosh Script:")
    print(script_content)
    
    # Execution Wrapper
    # We pipe this into docker exec
    import subprocess
    
    cmd = f"docker exec -i mongodb_shared mongosh -u {SHARED_MONGO_USER} -p {SHARED_MONGO_PASS} --authenticationDatabase admin"
    
    logger.info("Executing update on mongodb_shared...")
    process = subprocess.run(cmd, input=script_content, text=True, shell=True, capture_output=True)
    
    if process.returncode == 0:
        logger.info("Update Successful!")
        print(process.stdout)
    else:
        logger.error("Update Failed!")
        print(process.stderr)
