#!/bin/bash

# --- Jurisconsultor Test and Deploy Script ---

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
BACKEND_VENV_PATH="jurisconsultor/.venv/bin/python"
BACKEND_TEST_PATH="jurisconsultor/tests/"
FRONTEND_DIR="jurisconsultor/frontend"

# --- Functions ---
echo_green() {
    echo -e "\033[0;32m$1\033[0m"
}

echo_red() {
    echo -e "\033[0;31m$1\033[0m"
}

# --- Main Script ---

echo_green "Starting CI/CD pipeline for Test Environment..."

# 1. Run Backend Tests
echo_green "[1/4] Running backend tests..."
PYTHONPATH=jurisconsultor $BACKEND_VENV_PATH -m pytest $BACKEND_TEST_PATH
echo_green "Backend tests passed successfully."

# 2. Run Frontend Linter (as a stand-in for tests)
echo_green "[2/4] Running frontend linter..."
(cd $FRONTEND_DIR && npm install && npm run lint) # npm install to ensure deps are there
echo_green "Frontend linting passed successfully."


# 3. Build Docker Images
echo_green "[3/4] Building Docker images..."
docker compose build
echo_green "Docker images built successfully."

# 4. Deploy Services
echo_green "[4/4] Deploying services with Docker Compose..."
docker compose up -d

echo_green "\nDeployment to test environment completed successfully!"
echo "You can view the running services with: docker compose ps"

