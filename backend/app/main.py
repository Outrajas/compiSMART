# backend/app/main.py
import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.routes import ingest, chat, analytics
from app.db.sqlite import init_db
from app.core.config import settings
from app.core.logger import logger

app = FastAPI(title="CompiSmart Server Core", version="1.0.0")

# 1. Secured Security Configurations pulled from .env file architecture
# Using your established configuration engine management (settings) to load variables dynamically
DEMO_USERNAME = getattr(settings, "demo_username", None) or "admin"
DEMO_PASSWORD = getattr(settings, "demo_password", None) or "techsolve_secure_2026"

security = HTTPBasic()

def authenticate_private_demon(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, DEMO_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, DEMO_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid private credentials provided.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# 2. Configure Cross-Origin Resource Sharing (CORS) Bounds
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Secure Core Application Routing Subsystems via Enforced Global Dependency Injection
app.include_router(ingest.router, dependencies=[Depends(authenticate_private_demon)])
app.include_router(chat.router, dependencies=[Depends(authenticate_private_demon)])
app.include_router(analytics.router, dependencies=[Depends(authenticate_private_demon)])

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing system architecture requirements...")
    init_db()

@app.get("/health")
async def health_check():
    # Publicly accessible health probe endpoint for deployment container layers
    return {"status": "healthy", "scope": "isolated-demonstration"}