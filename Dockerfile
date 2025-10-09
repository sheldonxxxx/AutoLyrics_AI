# Multi-stage Dockerfile for Music Lyrics Processing Pipeline
# Following uv best practices for Python package management

FROM python:3.13-slim AS builder

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set up build environment
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv
# This creates a virtual environment at /app/.venv
RUN uv sync --frozen --no-install-project --no-dev

# Production stage
FROM python:3.13-slim AS runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libsox-fmt-all \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r lyrics && useradd -r -g lyrics lyrics

# Copy uv binary for runtime use
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set up application directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=lyrics:lyrics /app/.venv /app/.venv

# Copy application code
COPY --chown=lyrics:lyrics . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/input /app/output /app/tmp /app/models && \
    chown -R lyrics:lyrics /app

# Switch to non-root user
USER lyrics

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    # Default input/output directories
    INPUT_DIR=/app/input \
    OUTPUT_DIR=/app/output \
    TEMP_DIR=/app/tmp

# Create cache directory
RUN mkdir -p $UV_CACHE_DIR && chown lyrics:lyrics $UV_CACHE_DIR

# Default command - can be overridden
CMD ["python", "-m", "uv", "run", "process_lyrics.py", "--help"]