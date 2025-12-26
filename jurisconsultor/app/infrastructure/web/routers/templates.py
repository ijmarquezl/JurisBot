import os
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from domain.models.models import UserInDB
from infrastructure.web.dependencies import get_current_user
import infrastructure.ai.tools as tools
import json

router = APIRouter(
    prefix="/templates",
    tags=["templates"],
)

BASE_DOCS_PATH = "/docs" # Mounted volume path

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_template(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Uploads a .docx template to the tenant's specific folder.
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Only .docx files are allowed.")
    
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User is not associated with a company.")

    tenant_id = str(current_user.company_id)
    template_dir = os.path.join(BASE_DOCS_PATH, tenant_id, "templates")
    os.makedirs(template_dir, exist_ok=True)
    
    file_path = os.path.join(template_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
        
    return {"filename": file.filename, "message": "Template uploaded successfully."}

@router.get("/", response_model=List[str])
def list_templates(current_user: UserInDB = Depends(get_current_user)):
    """
    Lists available templates for the tenant.
    """
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User is not associated with a company.")

    tenant_id = str(current_user.company_id)
    template_dir = os.path.join(BASE_DOCS_PATH, tenant_id, "templates")
    
    if not os.path.exists(template_dir):
        return []
        
    templates = [f for f in os.listdir(template_dir) if f.endswith('.docx')]
    return templates

@router.get("/{template_name}/placeholders", response_model=List[str])
def get_placeholders_for_template(template_name: str, current_user: UserInDB = Depends(get_current_user)):
    """Returns the list of placeholders for a given template name."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User is not associated with a company.")

    # Set the tenant context in tools
    tools.set_tenant_id(str(current_user.company_id))
    
    result_str = tools.get_template_placeholders(template_name)
    result = json.loads(result_str)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
