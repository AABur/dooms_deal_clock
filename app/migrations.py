"""Database migrations for adding image_data field."""

from loguru import logger
from sqlalchemy import text

from app.models import engine


def add_image_data_column():
    """Add image_data column to clock_updates table if it doesn't exist."""
    try:
        with engine.connect() as connection:
            # Check if column exists
            result = connection.execute(
                text("SELECT name FROM pragma_table_info('clock_updates') WHERE name='image_data'")
            )

            if not result.fetchone():
                # Add the column
                connection.execute(text("ALTER TABLE clock_updates ADD COLUMN image_data TEXT"))
                connection.commit()
                logger.info("Added image_data column to clock_updates table")
            else:
                logger.info("image_data column already exists")

    except Exception as e:
        logger.error(f"Error adding image_data column: {e}")
        raise


def run_migrations():
    """Run all pending migrations."""
    logger.info("Running database migrations...")
    add_image_data_column()
    logger.info("Database migrations completed")
