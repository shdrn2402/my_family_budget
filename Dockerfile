# Start with slim Python 3.12 image
FROM python:3.12-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory
WORKDIR /app

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy dependency files first (better layer caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev

# Create log directory
RUN mkdir /logs

# Copy application files
COPY bot/ ./bot/
COPY scripts/ ./scripts/
COPY main.py ./main.py

# Set entry point
ENTRYPOINT ["python", "main.py"]
