from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.ingest import router as ingest_router
from app.routes.search import router as search_router
from app.routes.metadata import router as metadata_router
from app.routes.chat import router as chat_router
from app.core.config import settings
from app.core.logger import logger
from app.db.sqlite import init_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(search_router)
app.include_router(metadata_router)
app.include_router(chat_router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    init_db()

@app.get("/")
async def root():
    return {"app": settings.app_name}