from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pymongo.database import Database
from typing import List
import csv
import io

from models import (
    ScrapingSourceCreate, 
    ScrapingSourceUpdate, 
    ScrapingSourceInDB, 
    UserInDB,
    PyObjectId
)
from dependencies import get_db, get_admin_user

router = APIRouter(
    prefix="/sources",
    tags=["sources"],
    dependencies=[Depends(get_admin_user)], # Protect all routes in this router
)

SOURCES_COLLECTION = "scraping_sources"

@router.post("/upload_csv", status_code=status.HTTP_201_CREATED)
async def upload_sources_csv(
    file: UploadFile = File(...),
    db: Database = Depends(get_db)
):
    """
    Upload a CSV file to bulk-create scraping sources.
    The CSV must have a header row with at least 'name' and 'url'.
    Optional headers: 'scraper_type', 'pdf_direct_url', 'pdf_link_contains', 'pdf_link_ends_with'.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    content = await file.read()
    stream = io.StringIO(content.decode("utf-8"))
    reader = csv.DictReader(stream)

    sources_to_create = []
    required_fields = ['name', 'url']
    
    for row in reader:
        if not all(field in row for field in required_fields):
            raise HTTPException(status_code=400, detail=f"CSV row is missing one of the required fields: {required_fields}. Row: {row}")
        
        source_data = {
            "name": row.get("name"),
            "url": row.get("url"),
            "scraper_type": row.get("scraper_type", "generic_html"),
            "pdf_direct_url": row.get("pdf_direct_url"),
            "pdf_link_contains": row.get("pdf_link_contains"),
            "pdf_link_ends_with": row.get("pdf_link_ends_with"),
            "status": "pending", # Default status
        }
        sources_to_create.append(ScrapingSourceCreate(**source_data).dict())

    if not sources_to_create:
        raise HTTPException(status_code=400, detail="CSV file is empty or contains no data.")

    result = db[SOURCES_COLLECTION].insert_many(sources_to_create)
    
    return {"message": f"Successfully created {len(result.inserted_ids)} new sources."}


@router.post("/", response_model=ScrapingSourceInDB, status_code=status.HTTP_201_CREATED)
def create_source(
    source: ScrapingSourceCreate, 
    db: Database = Depends(get_db)
):
    """
    Create a new scraping source. (Admin only)
    """
    source_dict = source.dict()
    result = db[SOURCES_COLLECTION].insert_one(source_dict)
    created_source = db[SOURCES_COLLECTION].find_one({"_id": result.inserted_id})
    return ScrapingSourceInDB(**created_source)

@router.get("/", response_model=List[ScrapingSourceInDB])
def list_sources(db: Database = Depends(get_db)):
    """
    List all scraping sources. (Admin only)
    """
    sources = db[SOURCES_COLLECTION].find()
    return [ScrapingSourceInDB(**s) for s in sources]

@router.get("/{source_id}", response_model=ScrapingSourceInDB)
def get_source(source_id: PyObjectId, db: Database = Depends(get_db)):
    """
    Get a single scraping source by its ID. (Admin only)
    """
    source = db[SOURCES_COLLECTION].find_one({"_id": source_id})
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return ScrapingSourceInDB(**source)

@router.put("/{source_id}", response_model=ScrapingSourceInDB)
def update_source(
    source_id: PyObjectId,
    source_update: ScrapingSourceUpdate,
    db: Database = Depends(get_db)
):
    """
    Update a scraping source. (Admin only)
    """
    update_data = source_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    result = db[SOURCES_COLLECTION].update_one(
        {"_id": source_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Source not found")

    updated_source = db[SOURCES_COLLECTION].find_one({"_id": source_id})
    return ScrapingSourceInDB(**updated_source)

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: PyObjectId, db: Database = Depends(get_db)):
    """
    Delete a scraping source. (Admin only)
    """
    result = db[SOURCES_COLLECTION].delete_one({"_id": source_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Source not found")
    return
