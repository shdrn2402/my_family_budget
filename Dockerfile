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

# Install postgresql-client-18 for pg_dump
RUN apt-get update && apt-get install -y wget gnupg2 lsb-release && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg && \
    echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && apt-get install -y postgresql-client-18 && \
    rm -rf /var/lib/apt/lists/*

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
