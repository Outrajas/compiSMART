import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.routes import ingest, chat, analytics
from app.db.sqlite import init_db, get_connection
from app.services.vector_store_service import VectorStoreService
from app.core.config import settings
from app.core.logger import logger

app = FastAPI(title="CompiSmart Server Core", version="1.0.0")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, dependencies=[Depends(authenticate_private_demon)])
app.include_router(chat.router, dependencies=[Depends(authenticate_private_demon)])
app.include_router(analytics.router, dependencies=[Depends(authenticate_private_demon)])

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing system architecture requirements...")
    init_db()
    
    # Validation warmup (fast fail checks)
    try:
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        
        vs = VectorStoreService()
        vs.client.get_collections()  # Ping Qdrant
        logger.info("Startup validation passed: Database & Qdrant are responsive.")
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "scope": "isolated-demonstration"}