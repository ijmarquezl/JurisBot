# Jurisconsultor

Jurisconsultor is an AI-powered agent to help lawyers and law professionals in Mexico to efficiently query legal documents.

## Setup

1.  Create a virtual environment using `uv`:
    ```bash
    uv venv
    ```

2.  Activate the virtual environment:
    ```bash
    source .venv/bin/activate
    ```

3.  Install the dependencies:
    ```bash
    uv pip install -r requirements.txt
    ```

4.  Create a `.env` file based on the `.env.example` file and fill in the required credentials.

5.  Run the database migration:
    ```bash
    python db_migration.py
    ```

6.  Run the application:
    ```bash
    uvicorn app.main:app --reload
    ```
