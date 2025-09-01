"""FastAPI main application module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy.orm import Session

from app.migrations import run_migrations
from app.models import ClockUpdate, create_tables, get_db
from app.services.clock_service import ClockService
from app.utils.logging import setup_logging

setup_logging()

# Initialize clock service
clock_service = ClockService()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager.

    Args:
        app: FastAPI application instance

    Yields:
        None: Application startup and shutdown lifecycle
    """
    logger.info("Starting Dooms Deal Clock application")

    # Create database tables
    create_tables()
    logger.info("Database tables created")

    # Run migrations
    run_migrations()

    # Note: Background tasks not started automatically
    # Use POST /api/clock/fetch to manually fetch updates
    # or start background service via separate endpoint

    yield
    logger.info("Shutting down Dooms Deal Clock application")


app = FastAPI(
    title="Dooms Deal Clock",
    description="Web application for displaying Dooms Deal Clock updates from Telegram channel",
    version="0.1.0",
    lifespan=lifespan,
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
    """Root endpoint for API information.

    Returns:
        Dict[str, Any]: API status information
    """
    return {"message": "Dooms Deal Clock API", "status": "running"}


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for service monitoring.

    Returns:
        Dict[str, Any]: Service health status information
    """
    return {"status": "healthy", "service": "dooms-deal-clock", "version": "0.1.0"}


@app.get("/api/clock/latest")
async def get_latest_clock(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get the most recent clock update from database.

    Args:
        db: Database session dependency

    Returns:
        Dict[str, Any]: Latest clock update data including time, content, and image

    Raises:
        HTTPException: If no clock updates are found (404)
    """
    latest_update = clock_service.get_latest_update(db)

    if not latest_update:
        raise HTTPException(status_code=404, detail="No clock updates found")

    return {
        "id": latest_update.id,
        "time": latest_update.time_value,
        "content": latest_update.content,
        "image_data": latest_update.image_data,
        "created_at": latest_update.created_at.isoformat(),
        "message_id": latest_update.message_id,
    }


@app.get("/api/clock/history")
async def get_clock_history(limit: int = 10, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get paginated clock updates history.

    Args:
        limit: Maximum number of updates to return (default: 10)
        db: Database session dependency

    Returns:
        Dict[str, Any]: Clock updates history with pagination info
    """
    updates = clock_service.get_recent_updates(db, limit=limit)
    total_count = clock_service.get_updates_count(db)

    return {
        "updates": [
            {
                "id": update.id,
                "time": update.time_value,
                "content": update.content,
                "image_data": update.image_data,
                "created_at": update.created_at.isoformat(),
                "message_id": update.message_id,
            }
            for update in updates
        ],
        "total_count": total_count,
        "limit": limit,
    }


@app.post("/api/clock/fetch")
async def fetch_updates(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Manually trigger fetching new updates from Telegram channel.

    Args:
        db: Database session dependency

    Returns:
        Dict[str, Any]: Fetch operation result with updates count

    Raises:
        HTTPException: If fetching fails (500)
    """
    try:
        updates_count = await clock_service.fetch_and_store_updates(db)
        return {"message": f"Successfully fetched {updates_count} new updates", "updates_count": updates_count}
    except Exception as e:
        logger.error(f"Error fetching updates: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/clock/reload/{message_id}")
async def reload_message(message_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Force reload specific message with fresh image data from Telegram.

    Args:
        message_id: Telegram message ID to reload
        db: Database session dependency

    Returns:
        Dict[str, Any]: Reload operation result with updates count

    Raises:
        HTTPException: If reload operation fails (500)
    """
    try:
        # Delete existing message
        existing = db.query(ClockUpdate).filter(ClockUpdate.message_id == message_id).first()
        if existing:
            db.delete(existing)
            db.commit()
            logger.info(f"Deleted existing message {message_id}")

        # Fetch fresh data
        updates_count = await clock_service.fetch_and_store_updates(db)
        return {
            "message": f"Successfully reloaded message {message_id}, fetched {updates_count} updates",
            "message_id": message_id,
            "updates_count": updates_count,
        }
    except Exception as e:
        logger.error(f"Error reloading message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
