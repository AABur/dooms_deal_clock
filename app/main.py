"""FastAPI main application module."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from loguru import logger

from app.config import config
from app.models import create_tables, get_db
from app.services.clock_service import ClockService
from app.services.background_tasks import background_service
from app.utils.logging import setup_logging

setup_logging()

# Initialize clock service
clock_service = ClockService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Dooms Deal Clock application")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    # Note: Background tasks not started automatically
    # Use POST /api/clock/fetch to manually fetch updates
    # or start background service via separate endpoint
    
    yield
    logger.info("Shutting down Dooms Deal Clock application")


app = FastAPI(
    title="Dooms Deal Clock",
    description="Web application for displaying Dooms Deal Clock updates from Telegram channel",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="web"), name="static")


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {"message": "Dooms Deal Clock API", "status": "running"}


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "dooms-deal-clock",
        "version": "0.1.0"
    }


@app.get("/api/clock/latest")
async def get_latest_clock(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get the latest clock update."""
    latest_update = clock_service.get_latest_update(db)
    
    if not latest_update:
        raise HTTPException(status_code=404, detail="No clock updates found")
    
    return {
        "id": latest_update.id,
        "time": latest_update.time_value,
        "content": latest_update.content,
        "created_at": latest_update.created_at.isoformat(),
        "message_id": latest_update.message_id
    }


@app.get("/api/clock/history")
async def get_clock_history(
    limit: int = 10, 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get clock updates history."""
    updates = clock_service.get_recent_updates(db, limit=limit)
    total_count = clock_service.get_updates_count(db)
    
    return {
        "updates": [
            {
                "id": update.id,
                "time": update.time_value,
                "content": update.content,
                "created_at": update.created_at.isoformat(),
                "message_id": update.message_id
            }
            for update in updates
        ],
        "total_count": total_count,
        "limit": limit
    }


@app.post("/api/clock/fetch")
async def fetch_updates(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Manually trigger fetching updates from Telegram."""
    try:
        updates_count = await clock_service.fetch_and_store_updates(db)
        return {
            "message": f"Successfully fetched {updates_count} new updates",
            "updates_count": updates_count
        }
    except Exception as e:
        logger.error(f"Error fetching updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))