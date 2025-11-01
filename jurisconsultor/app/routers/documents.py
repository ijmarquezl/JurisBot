import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pymongo.database import Database
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi.responses import FileResponse

from models import GeneratedDocumentInDB, UserInDB, PyObjectId
from dependencies import get_db, get_current_user
from utils import answer_with_rag, search_raw_documents, get_public_db_conn # New import
import tools as legacy_tools

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

TEMPLATE_DIR = "../formatos/"

# --- Pydantic Models for Requests ---

class GenerateFromFormRequest(BaseModel):
    template_name: str
    project_id: PyObjectId
    document_name: str
    context: Dict[str, Any]

# --- Endpoints ---

@router.get("/templates", response_model=List[str])
def list_templates():
    """Lists all available .docx templates from the formats directory."""
    try:
        files = os.listdir(TEMPLATE_DIR)
        docx_files = [f for f in files if f.endswith('.docx')]
        return docx_files
    except FileNotFoundError:
        return []

@router.get("/templates/{template_name}/placeholders", response_model=List[str])
def get_placeholders_for_template(template_name: str):
    """Returns the list of placeholders for a given template name."""
    result_str = legacy_tools.get_template_placeholders(template_name)
    result = json.loads(result_str)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.post("/generate_from_form", response_model=GeneratedDocumentInDB)
def generate_document_from_form(
    request: GenerateFromFormRequest,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Orchestrates document generation from a form submission in a deterministic way."""
    context = request.context
    logger.info(f"Context received for document generation: {context}")
    logger.info(f"Checking RAG condition: ('lista_de_hechos' in context: {'lista_de_hechos' in context}) and (context['lista_de_hechos'] is truthy: {bool(context.get('lista_de_hechos'))})")
    
    # 1. If 'lista_de_hechos' (facts) are present, use RAG to find legal articles
    if 'lista_de_hechos' in context and context['lista_de_hechos']:
        rag_query = f"Based on the following facts: {context['lista_de_hechos']}, what legal articles and laws are applicable? Provide a concise list of articles and laws."
        logger.info(f"RAG Query: {rag_query}")
        legal_articles = answer_with_rag(rag_query)
        logger.info(f"RAG Result (legal_articles): {legal_articles}")
        # Assign the RAG findings to the most relevant placeholder
        context["articulos_aplicables"] = legal_articles
        logger.info(f"Context after RAG: {context}")

    # 2. Call the tool to fill the template and save the document file
    result_str = legacy_tools.fill_template_and_save_document(
        template_name=request.template_name,
        document_name=request.document_name,
        context=context
    )
    result = json.loads(result_str)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # 3. Create the document record in the database
    file_path = result.get("file_path")
    if not file_path:
        raise HTTPException(status_code=500, detail="Tool failed to return a file path.")

    doc_data = {
        "file_name": request.document_name,
        "project_id": request.project_id,
        "owner_email": current_user.email,
        "file_path": file_path,
        "is_archived": False, # New field for archiving
    }
    
    insert_result = db.generated_documents.insert_one(doc_data)
    created_doc = db.generated_documents.find_one({"_id": insert_result.inserted_id})

    if not created_doc:
        raise HTTPException(status_code=500, detail="Failed to create and retrieve document record from database.")

    return GeneratedDocumentInDB(**created_doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_generated_document(
    document_id: PyObjectId,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Deletes a generated document and its record from the database."""
    # 1. Fetch the document record
    document = db.generated_documents.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 2. Check permissions
    # Owner, Project Lead (of the document's project), or Admin can delete
    can_delete = (
        document["owner_email"] == current_user.email or
        current_user.role == "admin" or
        (
            current_user.role == "lead" and
            db.projects.find_one({"_id": document["project_id"], "members": current_user.email})
        )
    )
    if not can_delete:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document.")

    # 3. Delete the physical file
    if os.path.exists(document["file_path"]):
        try:
            os.remove(document["file_path"])
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete physical file: {e}")

    # 4. Delete the database record
    db.generated_documents.delete_one({"_id": document_id})

    return # 204 No Content


class ArchiveDocumentRequest(BaseModel):
    is_archived: bool

@router.put("/{document_id}/archive", response_model=GeneratedDocumentInDB)
def archive_generated_document(
    document_id: PyObjectId,
    request: ArchiveDocumentRequest,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Archives or unarchives a generated document."""
    # 1. Fetch the document record
    document = db.generated_documents.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 2. Check permissions
    # Owner, Project Lead (of the document's project), or Admin can archive/unarchive
    can_archive = (
        document["owner_email"] == current_user.email or
        current_user.role == "admin" or
        (
            current_user.role == "lead" and
            db.projects.find_one({"_id": document["project_id"], "members": current_user.email})
        )
    )
    if not can_archive:
        raise HTTPException(status_code=403, detail="Not authorized to archive/unarchive this document.")

    # 3. Update the archive status
    db.generated_documents.update_one(
        {"_id": document_id},
        {"$set": {"is_archived": request.is_archived, "last_updated": datetime.utcnow()}}
    )

    updated_document = db.generated_documents.find_one({"_id": document_id})
    return GeneratedDocumentInDB(**updated_document)


@router.get("/{document_id}/download", response_model=None) # Fixed: response_model=None
def download_generated_document(
    document_id: PyObjectId,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """Downloads a generated document."""
    # 1. Fetch the document record
    document = db.generated_documents.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 2. Check permissions (same as delete/archive)
    can_download = (
        document["owner_email"] == current_user.email or
        current_user.role == "admin" or
        (
            current_user.role == "lead" and
            db.projects.find_one({"_id": document["project_id"], "members": current_user.email})
        )
    )
    if not can_download:
        raise HTTPException(status_code=403, detail="Not authorized to download this document.")

    # 3. Return the file
    file_path = document["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical file not found on server.")

    return FileResponse(path=file_path, filename=document["file_name"], media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.get("/debug/search_raw_docs", response_model=List[Dict[str, Any]]) # New debug endpoint
def debug_search_raw_docs(
    query: str,
    db: Database = Depends(get_db),
):
    """Debug endpoint to search raw document content in PostgreSQL."""
    """Debug endpoint to search raw document content in PostgreSQL."""
    # This bypasses RAG and directly searches the content field in PostgreSQL
    try:
        conn = get_public_db_conn()
        cur = conn.cursor()
        # Using ILIKE for case-insensitive search
        cur.execute("SELECT content, source FROM documents WHERE content ILIKE %s LIMIT 10;", (f'%{query}%',))
        results = cur.fetchall()
        cur.close()
        conn.close()
        return [{'content': r[0], 'source': r[1]} for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching raw documents: {e}")


@router.get("/", response_model=List[GeneratedDocumentInDB])
def list_documents(
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
    include_archived: Optional[bool] = False # New parameter
):
    """Lists generated documents based on user role."""
    query = {}
    if current_user.role == "admin":
        company_projects = list(db.projects.find({"company_id": current_user.company_id}, {"_id": 1}))
        project_ids = [p["_id"] for p in company_projects]
        query = {"project_id": {"$in": project_ids}}
    elif current_user.role == "lead":
        lead_projects = list(db.projects.find({"members": current_user.email}, {"_id": 1}))
        project_ids = [p["_id"] for p in lead_projects]
        query = {"project_id": {"$in": project_ids}}
    else: # role == "member"
        query = {"owner_email": current_user.email}

    # Add filtering by archive status
    if not include_archived:
        query["is_archived"] = False

    documents_cursor = db.generated_documents.find(query).sort("created_at", -1)
    return [GeneratedDocumentInDB(**doc) for doc in documents_cursor]