import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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


class ClockUpdate(Base):
    """Модель для хранения обновлений часов"""

    __tablename__ = "clock_updates"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(String(8), nullable=False)  # Время в формате HH:MM:SS
    description = Column(Text, nullable=False)  # Описание ситуации
    raw_message = Column(Text, nullable=True)  # Исходное сообщение из Telegram
    message_id = Column(Integer, nullable=True)  # ID сообщения в Telegram
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Активная запись (последняя)


class ParsedMessage(Base):
    """Модель для логирования обработанных сообщений"""

    __tablename__ = "parsed_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, unique=True, nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_successfully = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)


# Create tables on module import
Base.metadata.create_all(bind=engine)


def create_tables():
    """Create database tables (for explicit calls)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
