import os
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.models import (
    GeneratedDocumentCreate,
    GeneratedDocumentInDB,
    UserInDB,
    PyObjectId,
)
from app.dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

GENERATED_DOCS_PATH = "documentos_generados/"

class RegisterDocumentRequest(BaseModel):
    file_name: str
    project_id: PyObjectId
    file_path: str

@router.post("/", response_model=GeneratedDocumentInDB, status_code=status.HTTP_201_CREATED)
def create_document(
    doc_in: GeneratedDocumentCreate,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Creates a new document record in the DB and a corresponding empty file.
    """
    # Verify the project exists and the user is a member of it
    project = db.projects.find_one({
        "_id": doc_in.project_id,
        "members": current_user.email
    })
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found or user is not a member.",
        )

    # Create the file path and the empty file
    file_name = f"{doc_in.file_name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
    file_path = os.path.join(GENERATED_DOCS_PATH, file_name)

    try:
        with open(file_path, "w") as f:
            f.write(f"# {doc_in.file_name}\n\n") # Create file with a title
    except IOError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create document file: {e}",
        )

    # Create the DB record
    doc_data = doc_in.dict()
    doc_data["owner_email"] = current_user.email
    doc_data["file_path"] = file_path
    
    result = db.generated_documents.insert_one(doc_data)
    created_doc = db.generated_documents.find_one({"_id": result.inserted_id})

    return GeneratedDocumentInDB(**created_doc)

@router.post("/register", response_model=GeneratedDocumentInDB, status_code=status.HTTP_201_CREATED)
def register_document(
    doc_in: RegisterDocumentRequest,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Registers a pre-generated document file in the database.
    This is intended to be called by an internal tool after a document has been created from a template.
    """
    # Verify the project exists and the user is a member of it
    project = db.projects.find_one({
        "_id": doc_in.project_id,
        "members": current_user.email
    })
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found or user is not a member.",
        )

    # Create the DB record
    doc_data = doc_in.dict()
    doc_data["owner_email"] = current_user.email
    
    result = db.generated_documents.insert_one(doc_data)
    created_doc = db.generated_documents.find_one({"_id": result.inserted_id})

    return GeneratedDocumentInDB(**created_doc)


@router.get("/", response_model=List[GeneratedDocumentInDB])
def list_documents(
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    List generated documents based on user role:
    - Admin: sees all documents in their company.
    - Lead: sees all documents in projects they are a member of.
    - Member: sees only documents they own.
    """
    query = {}
    if current_user.role == "admin":
        # Find all projects in the admin's company to get their IDs
        company_projects = list(db.projects.find({"company_id": current_user.company_id}, {"_id": 1}))
        project_ids = [p["_id"] for p in company_projects]
        query = {"project_id": {"$in": project_ids}}

    elif current_user.role == "lead":
        # Find all projects the lead is a member of
        lead_projects = list(db.projects.find({"members": current_user.email}, {"_id": 1}))
        project_ids = [p["_id"] for p in lead_projects]
        query = {"project_id": {"$in": project_ids}}
        
    else: # role == "member"
        query = {"owner_email": current_user.email}

    documents_cursor = db.generated_documents.find(query).sort("created_at", -1)
    return [GeneratedDocumentInDB(**doc) for doc in documents_cursor]