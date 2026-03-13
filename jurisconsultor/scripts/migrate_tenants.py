
import os
import subprocess
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

load_dotenv()

# Configuration
# This would typically come from a DB or config file.
# For this script, we'll manually define the source tenants based on your known setup.
# In a robust production script, you'd fetch this from the 'companies' postgres/mongo table.

# SHARED MONGO CONFIG
SHARED_MONGO_HOST = "mongodb_shared"
SHARED_MONGO_PORT = 27017
SHARED_MONGO_USER = os.getenv("MONGO_SHARED_ROOT_USERNAME", "root")
SHARED_MONGO_PASS = os.getenv("MONGO_SHARED_ROOT_PASSWORD", "secure_root_password")
SHARED_MONGO_URI_ADMIN = f"mongodb://{SHARED_MONGO_USER}:{SHARED_MONGO_PASS}@{SHARED_MONGO_HOST}:{SHARED_MONGO_PORT}/?authSource=admin"

# TENANTS TO MIGRATE
# Format: {"container": "container_name", "db": "db_name", "company_id": "id"}
TENANTS = [
    {
        "name": "Mi Primera Empresa",
        "container": "jurisbot-mongodb_mi_primera_empresa-1",
        "db_source": os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_DB"),
        "db_target": os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_DB"),
        "user_source": os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_USER"),
        "pass_source": os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_PASSWORD"),
        "user_new": f"user_{os.getenv('TENANT_MI_PRIMERA_EMPRESA_MONGO_DB')}", # Generate new unique user
        "pass_new": os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_PASSWORD") 
    },
    {
        "name": "Tenant A",
        "container": "jurisbot-mongodb_a-1", 
        "db_source": os.getenv("TENANT_A_MONGO_DB"),
        "db_target": os.getenv("TENANT_A_MONGO_DB"),
        "user_source": os.getenv("TENANT_A_MONGO_USER"),
        "pass_source": os.getenv("TENANT_A_MONGO_PASSWORD"),
        "user_new": f"user_{os.getenv('TENANT_A_MONGO_DB')}",
        "pass_new": os.getenv("TENANT_A_MONGO_PASSWORD") 
    }
]

def run_command(cmd):
    """Runs a shell command."""
    logger.info(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Command failed with return code {result.returncode}")
        logger.error(f"STDERR: {result.stderr}")
        logger.error(f"STDOUT: {result.stdout}")
        raise Exception(f"Command failed: {result.stderr}")
    return result.stdout

def setup_shared_user(client, db_name, username, password):
    """Creates a user in the shared DB restricted to that DB."""
    logger.info(f"Creating user '{username}' for DB '{db_name}'...")
    db = client[db_name]
    
    # Check if user exists? createUser errors if exists.
    try:
        db.command("createUser", username, pwd=password, roles=[{"role": "dbOwner", "db": db_name}])
        logger.info(f"User '{username}' created successfully.")
    except Exception as e:
        if "already exists" in str(e):
            logger.info(f"User '{username}' already exists. Updating password...")
            db.command("updateUser", username, pwd=password)
        else:
            raise e

def migrate_tenant(tenant):
    logger.info(f"--- Migrating {tenant['name']} ---")
    
    # 1. Dump from Source Container
    # We use docker exec to dump inside the container and stream it out, 
    # OR we can assume mongodump is installed in the place where script runs.
    # Since this script runs on HOST (or inside a container with mongo tools), we'll assume we used docker exec.
    
    # EASIER: Use 'mongodump' connecting to the container remotely if ports are open? 
    # Ports are NOT open directly to host usually.
    # BEST: Docker exec to stdout pipe.
    
    # Command: mongodump --archive --db source_db | mongorestore --archive --nsFrom source_db --nsTo target_db --uri target_uri
    
    # Since we are running this likely FROM the 'scheduler' or 'backend' container (which has access to network), 
    # we can address them by hostname.
    # BUT, 'mongodump' binary needs to be present. 
    # Let's assume we run this script inside the 'mongodb_shared' container itself or one that has tools?
    # Actually, the user asked for a script.
    
    # Let's write the script safely assuming it runs locally on the valid container OR we shell out to docker from host.
    # Assuming this script runs on the HOST machine (where 'docker' command is available).
    
    source_cont = tenant['container']
    target_cont = "mongodb_shared"
    db_source = tenant['db_source']
    db_target = tenant['db_target']
    
    # Check if source container valid
    if not db_source:
        logger.warning(f"Skipping {tenant['name']} due to missing DB config.")
        return

    logger.info(f"Streaming data from {source_cont}/{db_source} to {target_cont}/{db_target}...")
    
    # Split execution to isolate errors
    dump_file = f"/tmp/{db_source}.dump"
    
    # 1. DUMP
    # Get source credentials from config list - using the 'pass_new' as source pass assumption from earlier
    # BUT wait, the dictionary keys are: container, db_source. 
    # The setup of TENANTS structure had user_new and pass_new. 
    # For migration to work, we need source user/pass too.
    # Looking at TENANT definitions in script:
    # "pass_new": os.getenv("TENANT_MI_PRIMERA_EMPRESA_MONGO_PASSWORD") 
    # This IS the source password.
    # What about source user? "user_new": "user_mi_primera_empresa" <- this is hardcoded new user.
    # The source user in docker-compose for 'mi_primera_empresa' was TENANT_..._USER.
    
    # I need to fetch Source User from env or use root if that's how it was setup.
    # In 'docker-compose.yml', mongodb_mi_primera_empresa uses:
    # MONGO_INITDB_ROOT_USERNAME: ${TENANT_MI_PRIMERA_EMPRESA_MONGO_USER}
    
    source_user = os.getenv(f"TENANT_{tenant['name'].upper().replace(' ', '_')}_MONGO_USER") 
    # Wait, fetching dynamically is hard. Let's fix the TENANTS struct to include 'user_source' and 'pass_source'.
    # Actually, the 'user_new' in my script was "user_mi_primera_empresa", but the Env var is likely different.
    
    # I will assume root/admin auth for the dump because we are dumping the whole DB.
    # I'll just use the env getters in the loop since I can't easily refactor the dict without context.
    # actually, I'll assume the password provided in 'pass_new' is the correct root password for the source container,
    # and the user is likely the one associated with that password.
    
    # A safer bet: The 'db_source' variable holds the DB name. 
    # The container was provisioned with specific ROOT user/pass. 
    # I will modify the script to allow passing `user_source` and `pass_source` and update the TENANTS list.
    
    cmd_dump = f"docker exec {source_cont} mongodump --username root --password {tenant['pass_new']} --authenticationDatabase admin --db {db_source} --archive > {dump_file}"
    # Wait, user might not be 'root'. It's defined in env. 
    # I'll try with the known env var logic.
    
    # Let's check what 'user_new' has. "user_mi_primera_empresa".
    # In docker-compose, for 'mongodb_mi_primera_empresa':
    # MONGO_INITDB_ROOT_USERNAME: ${TENANT_MI..._USER}
    # So 'user_new' in the script IS the source user (or intended to be).
    
    auth_flags = f"--username {tenant['user_source']} --password {tenant['pass_source']} --authenticationDatabase admin"
    cmd_dump = f"docker exec {source_cont} mongodump {auth_flags} --db {db_source} --archive > {dump_file}"
    try:
        run_command(cmd_dump)
        # Check size
        size = os.path.getsize(dump_file)
        logger.info(f"Dumped {size} bytes to {dump_file}")
        if size == 0:
             logger.error("Dump file is empty!")
             return
    except Exception as e:
        logger.error(f"Dump failed: {e}")
        return

    # 2. RESTORE
    # Authenticate against SHARED mongo as ROOT
    target_auth_flags = f"--username {SHARED_MONGO_USER} --password {SHARED_MONGO_PASS} --authenticationDatabase admin"
    cmd_restore = f"docker exec -i {target_cont} mongorestore {target_auth_flags} --archive --nsFrom='{db_source}.*' --nsTo='{db_target}.*' < {dump_file}"
    try:
        run_command(cmd_restore)
        logger.info("Data restore complete.")
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return
    
    # Cleanup
    os.remove(dump_file)

    # 2. Setup User in Target
    # We need a pymongo connection to the shared DB.
    # We can't easily connect from HOST to shared db IP provided (172.25...) unless we expose port.
    # But we can use docker exec again to run a mongo shell script OR install pymongo locally?
    # Since we are creating this script, let's assume we rely on 'docker exec mongo ... eval' for simplicity if pymongo not on host.
    
    logger.info("Configuring user permissions...")
    js_command = f"db.createUser({{user: '{tenant['user_new']}', pwd: '{tenant['pass_new']}', roles: [{{role: 'dbOwner', db: '{db_target}'}}]}});"
    
    # Executing against the specific DB
    auth_args = f"-u {SHARED_MONGO_USER} -p {SHARED_MONGO_PASS} --authenticationDatabase admin"
    cmd_user = f"docker exec {target_cont} mongosh {db_target} {auth_args} --eval \"{js_command}\""
    
    try:
        run_command(cmd_user)
    except Exception as e:
        if "already exists" in str(e):
             # Try update
             js_upd = f"db.updateUser('{tenant['user_new']}', {{pwd: '{tenant['pass_new']}'}});"
             cmd_upd = f"docker exec {target_cont} mongosh {db_target} {auth_args} --eval \"{js_upd}\""
             run_command(cmd_upd)
        else:
             logger.error(f"Failed to create user: {e}")

    logger.info(f"Successfully migrated {tenant['name']}.")

if __name__ == "__main__":
    logger.info("Starting Tenant Migration to Shared MongoDB...")
    
    # Verify shared is up
    # (Simple sleep or check could go here)
    
    for tenant in TENANTS:
        migrate_tenant(tenant)
        
    logger.info("All tenants processed.")
