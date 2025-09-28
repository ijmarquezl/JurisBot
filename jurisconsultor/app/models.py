from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId # Keep ObjectId for manual conversion
from pydantic_core import core_schema

# Custom Pydantic type for ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

# Common Pydantic model configuration for DB models
model_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    json_encoders={ObjectId: str}, # This will convert ObjectId to str during serialization
    arbitrary_types_allowed=True,
)

# --- Company Models ---
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyInDB(CompanyBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')

# --- User Models ---
class UserBase(BaseModel):

    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    model_config = model_config
    password: str
    company_id: Optional[PyObjectId] = None

class UserUpdate(BaseModel):
    model_config = model_config
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    company_id: Optional[PyObjectId] = None
    role: Optional[str] = None

class UserInDB(UserBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')
    hashed_password: str
    company_id: Optional[PyObjectId] = None
    role: str = "member" # e.g., admin, lead, member

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
    id: PyObjectId = Field(alias='_id')
    company_id: PyObjectId
    owner_email: str
    members: List[str] = [] # List of member emails
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- Task Models ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"

class TaskCreate(TaskBase):
    pass

class TaskInDB(TaskBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')
    project_id: PyObjectId
    creator_email: str
    assignee_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)