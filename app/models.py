"""Database models for the Dooms Deal Clock application.

Modern layout: Base and DB session live in `app.db`, this module declares
SQLAlchemy models and re-exports `engine`, `SessionLocal`, `create_tables`,
and `get_db` for backwards compatibility.
"""

from typing import Generator

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.session import SessionLocal as _SessionLocal
from app.db.session import engine as _engine


class ClockUpdate(Base):  # type: ignore[misc, valid-type]
    """Model for storing clock updates from Telegram channel."""

    __tablename__ = "clock_updates"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    time_value = Column(String(50), nullable=True)
    image_data = Column(Text, nullable=True)  # Base64 encoded image data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<ClockUpdate(id={self.id}, time_value='{self.time_value}')>"


# Re-export engine and SessionLocal to keep existing imports working
engine = _engine
SessionLocal = _SessionLocal


def create_tables() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
