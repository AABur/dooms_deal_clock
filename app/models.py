"""Database models for the Dooms Deal Clock application."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from app.config import config

Base = declarative_base()


class ClockUpdate(Base):
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


# Create database engine and session
engine = create_engine(config.DATABASE_URL, echo=config.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()