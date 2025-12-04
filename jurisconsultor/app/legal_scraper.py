import os
import glob
import argparse
import logging
from pypdf import PdfReader
from utils import get_mongo_client, get_public_db_conn, get_private_db_conn, generate_embedding
import re

logger = logging.getLogger(__name__)

def delete_document_by_source(source_name: str, db_type: str, company_id: str = None):
    """
    Deletes all data associated with a specific source file from all databases.
    
    Args:
        source_name (str): The filename of the source to delete (e.g., 'ley_federal.pdf').
        db_type (str): The database type ('public' or 'private').
        company_id (str, optional): The company ID for private documents.
    """
    logger.info(f"Attempting to delete all data for source: {source_name}")
    
    # Get database connections
    mongo_client = get_mongo_client()
    db = mongo_client.jurisconsultor
    documents_collection = db.documents

    if db_type == 'public':
        conn = get_public_db_conn()
    elif db_type == 'private':
        conn = get_private_db_conn()
    else:
        raise ValueError("Invalid db_type specified. Must be 'public' or 'private'.")
        
    cur = conn.cursor()

    try:
        # 1. Delete from PostgreSQL 'documents' table
        cur.execute("DELETE FROM documents WHERE source = %s;", (source_name,))
        pg_deleted_count = cur.rowcount
        logger.info(f"Deleted {pg_deleted_count} chunks from PostgreSQL for source '{source_name}'.")

        # 2. Delete ownership record if private
        if company_id:
            cur.execute("DELETE FROM document_ownership WHERE source = %s AND company_id = %s;", (source_name, company_id))
            logger.info(f"Deleted ownership record from PostgreSQL for source '{source_name}'.")

        # 3. Delete from MongoDB 'documents' collection
        mongo_result = documents_collection.delete_many({"source": source_name, "company_id": company_id})
        logger.info(f"Deleted {mongo_result.deleted_count} metadata documents from MongoDB for source '{source_name}'.")
        
        conn.commit()
        logger.info(f"Successfully deleted all data for source: {source_name}")

    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred during deletion for source {source_name}: {e}", exc_info=True)
    finally:
        cur.close()
        conn.close()
        # mongo_client.close() # Removed: MongoClient should be managed by caller

def process_single_document(pdf_path: str, db_type: str, company_id: str = None):
    """
    Processes a single PDF document and stores its chunks and embeddings in the databases.
    """
    logger.info(f"Processing document: {pdf_path} for db: {db_type}, company: {company_id or 'public'}")
    
    mongo_client = get_mongo_client()
    db = mongo_client.jurisconsultor
    documents_collection = db.documents

    if db_type == 'public':
        conn = get_public_db_conn()
    elif db_type == 'private':
        conn = get_private_db_conn()
    else:
        raise ValueError("Invalid db_type specified. Must be 'public' or 'private'.")
        
    cur = conn.cursor()

    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        chunks = re.split(r'(?=Artículo \d+\.?-?)', text)
        processed_chunks = [c.strip() for c in chunks if len(c.strip()) > 50]

        source_name = os.path.basename(pdf_path)

        for i, chunk in enumerate(processed_chunks):
            embedding = generate_embedding(chunk)
            
            cur.execute(
                "INSERT INTO documents (content, embedding, source) VALUES (%s, %s, %s) RETURNING id;",
                (chunk, embedding.tolist(), source_name)
            )
            document_id = cur.fetchone()[0]

            if company_id:
                cur.execute(
                    "INSERT INTO document_ownership (source, company_id) VALUES (%s, %s) ON CONFLICT (source, company_id) DO NOTHING;",
                    (source_name, company_id)
                )

            mongo_doc = {
                "source": source_name,
                "chunk_index": i,
                "postgres_id": document_id,
                "db_type": db_type,
                "company_id": company_id
            }
            documents_collection.insert_one(mongo_doc)
        
        logger.info(f"Stored {len(processed_chunks)} chunks for document '{source_name}'.")
        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to process document {pdf_path}: {e}", exc_info=True)
    finally:
        cur.close()
        conn.close()
        # mongo_client.close() # Removed: MongoClient should be managed by caller

def process_document_directory(pdf_directory: str, db_type: str, company_id: str = None):
    """
    Processes and stores all legal documents from a directory into the specified database.
    """
    pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in the '{pdf_directory}' directory.")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process in '{pdf_directory}'.")
    for pdf_path in pdf_files:
        process_single_document(pdf_path, db_type, company_id)
    
    logger.info("\nProcessing complete for directory.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process PDF documents and store them in a database.")
    parser.add_argument("directory", type=str, help="The path to the directory containing the PDF files.")
    parser.add_argument("db_type", type=str, choices=['public', 'private'], help="The type of database to use ('public' or 'private').")
    parser.add_argument("--company-id", type=str, help="The company ID to associate these documents with (for private docs).")
    
    args = parser.parse_args()
    
    # Renamed original function to avoid confusion
    process_document_directory(args.directory, args.db_type, args.company_id)
