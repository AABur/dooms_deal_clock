# Use official Python image
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash clockapp

# Install uv package manager
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache-dir \
    fastapi uvicorn[standard] telethon python-dotenv \
    sqlalchemy aiofiles httpx pydantic loguru

# Copy source code
COPY . .

# Install package in development mode
RUN uv pip install --system --no-cache-dir -e . --no-deps

# Create directories for data and set permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R clockapp:clockapp /app

# Switch to non-root user
USER clockapp

# Configure environment variables
ENV DATA_DIR=/app/data
ENV DATABASE_URL=sqlite:///./data/clock_data.db

# Configure volumes for persistent data
VOLUME ["/app/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app'); from app.config import config; print('OK')" || exit 1

# Default command
CMD ["python", "run.py"]