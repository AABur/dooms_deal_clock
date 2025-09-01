import os
import sys
from datetime import datetime
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Load configuration
load_dotenv()

# Use in-memory SQLite for testing environment to avoid file creation issues
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clock_data.db")

# Force in-memory database during tests
if "pytest" in sys.modules or any("test" in arg for arg in sys.argv):
    DATABASE_URL = "sqlite:///:memory:"

# Create engine with appropriate settings
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ClockUpdate(Base):  # type: ignore[misc, valid-type]
    """Model for storing clock updates."""

    __tablename__ = "clock_updates"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(String(8), nullable=False)  # Time in HH:MM:SS
    description = Column(Text, nullable=False)  # Description
    raw_message = Column(Text, nullable=True)  # Original Telegram message
    message_id = Column(Integer, nullable=True)  # Telegram message ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Active (latest) record flag


class ParsedMessage(Base):  # type: ignore[misc, valid-type]
    """Model for logging processed messages."""

    __tablename__ = "parsed_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, unique=True, nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_successfully = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)


# Create tables on module import
Base.metadata.create_all(bind=engine)


def create_tables() -> None:
    """Create database tables (for explicit calls)."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session (FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
