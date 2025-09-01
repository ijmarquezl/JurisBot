import logging
from logging.config import dictConfig
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pymongo.database import Database
from jose import JWTError
from pydantic import BaseModel
from typing import Optional, List

from app.logging_config import LOGGING_CONFIG
from app.rag_agent import run_agent
from app.models import UserCreate, UserInDB, Token, TokenData, UserBase
from app.security import create_access_token, create_refresh_token, verify_password, verify_token
from app.users import create_user, get_user
from app.utils import get_mongo_client
from app.routers import projects, tasks, admin
from app.dependencies import get_db, get_current_user, oauth2_scheme

# Apply logging configuration
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Jurisconsultor API",
    description="API for the Jurisconsultor AI agent.",
    version="0.4.0",
)

# --- CORS Middleware ---
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown.")

# --- API Routers ---
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(admin.router)

@app.post("/users/register", response_model=UserBase)
def register(user: UserCreate, db: Database = Depends(get_db)):
    """Register a new user."""
    logger.info(f"Registering new user: {user.email}")
    db_user = get_user(db, email=user.email)
    if db_user:
        logger.warning(f"Registration failed for email {user.email}: Email already registered.")
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    logger.info(f"User {user.email} registered successfully.")
    return new_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db)):
    """Login user and return access and refresh tokens."""
    logger.info(f"Login attempt for user: {form_data.username}")
    user = get_user(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    logger.info(f"User {form_data.username} logged in successfully.")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@app.post("/refresh", response_model=Token)
def refresh_access_token(refresh_token: str = Body(..., embed=True), db: Database = Depends(get_db)):
    """Refresh an access token."""
    logger.info("Attempting to refresh access token.")
    try:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type for refresh.")
            raise HTTPException(status_code=401, detail="Invalid token type")
        email = payload.get("sub")
        if email is None:
            logger.warning("Invalid token: no email subject.")
            raise HTTPException(status_code=401, detail="Invalid token")
        user = get_user(db, email=email)
        if user is None:
            logger.warning(f"User not found for token refresh: {email}")
            raise HTTPException(status_code=401, detail="User not found")
        
        new_access_token = create_access_token(data={"sub": user.email})
        logger.info(f"Token refreshed successfully for user: {email}")
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except JWTError:
        logger.error("Invalid refresh token.", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.get("/users/me", response_model=UserBase)
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Get the current logged-in user."""
    return current_user

class AskRequest(BaseModel):
    question: str
    history: Optional[List[str]] = None

@app.get("/")
def read_root():
    """
    Root endpoint for health checks.
    """
    return {"status": "ok"}

@app.post("/ask")
def ask(request: AskRequest, token: str = Depends(oauth2_scheme)):
    """
    Endpoint to interact with the conversational agent.
    """
    user = get_current_user(token, get_db())
    logger.info(f"User {user.email} is asking: '{request.question}'")
    answer = run_agent(user_query=request.question, history=request.history, auth_token=token)
    logger.info(f"Agent provided answer to {user.email}.")
    return {"answer": answer}