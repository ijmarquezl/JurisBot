from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pymongo.database import Database
from typing import List
import csv
import io
import re

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

def _generate_filename(name: str) -> str:
    """Sanitizes a string to be a valid filename."""
    if not name:
        return "unnamed_source.pdf"
    # Lowercase, replace spaces and invalid chars with underscores
    s = name.lower().strip()
    s = re.sub(r'\s+', '_', s)
    s = re.sub(r'[^a-z0-9_.]', '', s)
    # Ensure it ends with .pdf, but don't double-add it
    if s.endswith('.pdf'):
        return s
    return f"{s}.pdf"


@router.post("/upload_csv", status_code=status.HTTP_201_CREATED)
async def upload_sources_csv(
    file: UploadFile = File(...),
    db: Database = Depends(get_db)
):
    """
    Upload a CSV file to bulk-create scraping sources.
    The CSV must have a header row. The 'name' (or 'Nombre') column is required.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    content = await file.read()
    stream = io.StringIO(content.decode("utf-8"))
    
    try:
        reader = csv.DictReader(stream)
        sources_to_create = []
        
        for row in reader:
            source_name = row.get("name") or row.get("Nombre")
            if not source_name:
                raise HTTPException(
                    status_code=400, 
                    detail=f"CSV row is missing the required 'name' or 'Nombre' field. Row: {row}"
                )

            # Create the Pydantic model directly from the row data for validation
            source_model = ScrapingSourceCreate(
                name=source_name,
                url=row.get("url") or row.get("URL"),
                scraper_type=row.get("scraper_type") or row.get("Tipo de Scraper"),
                pdf_direct_url=row.get("pdf_direct_url") or row.get("URL directa a PDF"),
                pdf_link_contains=row.get("pdf_link_contains") or row.get("PDF Link contiene"),
                pdf_link_ends_with=row.get("pdf_link_ends_with") or row.get("PDF Link termina con"),
                local_filename=row.get("local_filename") or row.get("Nombre de archivo local")
            )

            # Now, apply the generation logic to the model instance
            if not source_model.local_filename:
                source_model.local_filename = _generate_filename(source_model.name)

            # Append the dictionary created from the final, validated model
            # Using exclude_unset=True is cleaner than manual dict cleaning
            sources_to_create.append(source_model.dict(exclude_unset=True))

    except csv.Error as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV file: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing row or data validation: {e}")

    if not sources_to_create:
        raise HTTPException(status_code=400, detail="CSV file is empty or contains no valid data.")

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
    if not source.local_filename:
        source.local_filename = _generate_filename(source.name)
        
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

    # If name is updated, we might need to update the filename if it's not explicitly provided
    if "name" in update_data and "local_filename" not in update_data:
        update_data["local_filename"] = _generate_filename(update_data["name"])

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