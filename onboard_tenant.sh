#!/bin/bash

# --- Tenant Onboarding Script ---
set -e

# --- Usage ---
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <company_name> <admin_email> <admin_password>"
    exit 1
fi

# --- Input Variables ---
COMPANY_NAME=$1
ADMIN_EMAIL=$2
ADMIN_PASSWORD=$3
TENANT_ID=$(echo "$COMPANY_NAME" | tr '[:upper:]' '[:lower:]' | sed -e 's/[^a-z0-9] /_/g' -e 's/ /_/g')
TENANT_ID_UPPER=$(echo "$TENANT_ID" | tr '[:lower:]' '[:upper:]')

echo "--- Starting onboarding for new tenant: $COMPANY_NAME (ID: $TENANT_ID) ---"

# --- Generate Secure Passwords ---
generate_password() {
    if command -v openssl &> /dev/null; then
        openssl rand -base64 12
    else
        date +%s | sha256sum | base64 | head -c 12
    fi
}
POSTGRES_PASSWORD=$(generate_password)
MONGO_PASSWORD=$(generate_password)
echo "Generated secure database passwords."

# --- Update .env file ---
ENV_FILE=".env"
echo "Updating $ENV_FILE..."
cat >> $ENV_FILE << EOL

# --- Credentials for Tenant: $TENANT_ID ---
TENANT_${TENANT_ID_UPPER}_POSTGRES_USER=${TENANT_ID}_user
TENANT_${TENANT_ID_UPPER}_POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
TENANT_${TENANT_ID_UPPER}_POSTGRES_DB=${TENANT_ID}_db
TENANT_${TENANT_ID_UPPER}_MONGO_USER=${TENANT_ID}_user
TENANT_${TENANT_ID_UPPER}_MONGO_PASSWORD=${MONGO_PASSWORD}
TENANT_${TENANT_ID_UPPER}_MONGO_DB=${TENANT_ID}_db
EOL
echo "Successfully updated $ENV_FILE."

# --- Generate Docker Compose Override ---
OVERRIDE_FILE="docker-compose.override.yml"
echo "Updating Docker Compose override file: $OVERRIDE_FILE..."

# Ensure the override file has the top-level keys. 2>/dev/null suppresses grep errors if file doesnt exist.
if ! grep -q "^services:" "$OVERRIDE_FILE" 2>/dev/null; then
    echo "services:" > "$OVERRIDE_FILE"
fi
if ! grep -q "^volumes:" "$OVERRIDE_FILE" 2>/dev/null; then
    echo -e "\nvolumes:" >> "$OVERRIDE_FILE"
fi

# Create temporary files for the new service and volume definitions
SERVICE_TMP=$(mktemp)
VOLUME_TMP=$(mktemp)

PG_USER_VAR="TENANT_${TENANT_ID_UPPER}_POSTGRES_USER"
PG_PASS_VAR="TENANT_${TENANT_ID_UPPER}_POSTGRES_PASSWORD"
PG_DB_VAR="TENANT_${TENANT_ID_UPPER}_POSTGRES_DB"
MONGO_USER_VAR="TENANT_${TENANT_ID_UPPER}_MONGO_USER"
MONGO_PASS_VAR="TENANT_${TENANT_ID_UPPER}_MONGO_PASSWORD"
MONGO_DB_VAR="TENANT_${TENANT_ID_UPPER}_MONGO_DB"

# Write service definitions to temp file
cat > $SERVICE_TMP << EOL
  postgres_${TENANT_ID}:
    image: postgres:13-alpine
    environment:
      POSTGRES_USER: \$${PG_USER_VAR}
      POSTGRES_PASSWORD: \$${PG_PASS_VAR}
      POSTGRES_DB: \$${PG_DB_VAR}
    volumes:
      - postgres_${TENANT_ID}_data:/var/lib/postgresql/data
    networks:
      - jurisconsultor-net

  mongodb_${TENANT_ID}:
    image: mongo:latest
    environment:
      MONGO_INITDB_ROOT_USERNAME: \$${MONGO_USER_VAR}
      MONGO_INITDB_ROOT_PASSWORD: \$${MONGO_PASS_VAR}
    volumes:
      - mongodb_${TENANT_ID}_data:/data/db
    networks:
      - jurisconsultor-net
EOL

# Write volume definitions to temp file
cat > $VOLUME_TMP << EOL
  postgres_${TENANT_ID}_data:
  mongodb_${TENANT_ID}_data:
EOL

# Use sed to insert the contents of the temp files under the correct keys
sed -i -e "/^services:/r $SERVICE_TMP" "$OVERRIDE_FILE"
sed -i -e "/^volumes:/r $VOLUME_TMP" "$OVERRIDE_FILE"

rm "$SERVICE_TMP" "$VOLUME_TMP"

echo "Successfully updated $OVERRIDE_FILE."

# --- Bring up all services --- 
echo "Applying changes and bringing up all services..."
source .env
docker compose up -d --remove-orphans

echo "Waiting 15 seconds for databases to initialize..."
sleep 15

# --- Create the Admin User ---
echo "Creating admin user: $ADMIN_EMAIL..."

MONGO_USER_VALUE=$(printenv $MONGO_USER_VAR)
MONGO_PASS_VALUE=$(printenv $MONGO_PASS_VAR)
MONGO_DB_VALUE=$(printenv $MONGO_DB_VAR)

NEW_TENANT_MONGO_URI="mongodb://${MONGO_USER_VALUE}:${MONGO_PASS_VALUE}@mongodb_${TENANT_ID}:27017/${MONGO_DB_VALUE}?authSource=admin"

docker exec \
  -e MONGO_URI="$NEW_TENANT_MONGO_URI" \
  -e MONGO_DB_NAME="$MONGO_DB_VALUE" \
  jurisbot-backend-1 \
  python app/create_admin.py "$ADMIN_EMAIL" "$ADMIN_PASSWORD"

echo "--- Onboarding for tenant '$COMPANY_NAME' complete! ---"
echo "You should now be able to log in with the email '$ADMIN_EMAIL'."