# ==============================================================================
# Voice AI Patient Registration System — Production Container Image
# Compatible with Hugging Face Spaces, Koyeb, Render, and Local Docker
# ==============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=7860 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Install system dependencies (curl for health checks, gcc/python3-dev for native C extensions like asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user (UID 1000 for Hugging Face Spaces compliance)
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install python dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code (filtered by .dockerignore)
COPY --chown=user:user . .

USER user

EXPOSE 7860

# Health check probe using dynamic PORT with fallback
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

# Production ASGI server entrypoint with dynamic PORT support for Hugging Face Spaces (7860) & Cloud
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
