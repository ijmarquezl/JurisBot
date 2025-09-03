from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId # Keep ObjectId for manual conversion

# Common Pydantic model configuration for DB models
model_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    json_encoders={ObjectId: str}, # This will convert ObjectId to str during serialization
)

# --- Company Models ---
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyInDB(CompanyBase):
    model_config = model_config
    id: str # Removed Field(alias="_id")

    @classmethod
    def from_mongo(cls, data: dict):
        if "_id" in data:
            data["id"] = str(data["_id"])
        return cls(**data)

# --- User Models ---
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    company_id: Optional[str] = None # Changed to str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    company_id: Optional[str] = None # Changed to str
    role: Optional[str] = None

class UserInDB(UserBase):
    model_config = model_config
    id: str # Removed Field(alias="_id")
    hashed_password: str
    company_id: Optional[str] = None
    role: str = "member"

    @classmethod
    def from_mongo(cls, data: dict):
        if "_id" in data:
            data["id"] = str(data["_id"])
        if "company_id" in data and data["company_id"] is not None:
            data["company_id"] = str(data["company_id"])
        return cls(**data)

# --- Token Models ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Project Models ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectInDB(ProjectBase):
    model_config = model_config
    id: str # Removed Field(alias="_id")
    company_id: str
    owner_email: str
    members: List[str] = [] # List of member emails
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_mongo(cls, data: dict):
        if "_id" in data:
            data["id"] = str(data["_id"])
        if "company_id" in data and data["company_id"] is not None:
            data["company_id"] = str(data["company_id"])
        return cls(**data)

# --- Task Models ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"

class TaskCreate(TaskBase):
    pass

class TaskInDB(TaskBase):
    model_config = model_config
    id: str # Removed Field(alias="_id")
    project_id: str
    creator_email: str
    assignee_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def from_mongo(cls, data: dict):
        if "_id" in data:
            data["id"] = str(data["_id"])
        if "project_id" in data and data["project_id"] is not None:
            data["project_id"] = str(data["project_id"])
        return cls(**data)