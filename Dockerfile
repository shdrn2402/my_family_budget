# Start with slim Python 3.12 image
FROM python:3.12-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Create a non-privileged user for security
RUN groupadd -r budget_group && useradd -r -g budget_group --no-create-home --shell /bin/false budget_user

# Set working directory
WORKDIR /app

# Create log directory and immediately give ownership to the non-privileged user
RUN mkdir /logs && chown budget_user:budget_group /logs

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

# Change ownership of the working directory to the new user
RUN chown -R budget_user:budget_group /app

# Switch to the new user
USER budget_user

# Copy dependency files first (better layer caching)
COPY --chown=budget_user:budget_group "pyproject.toml" "uv.lock" ".python-version" ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev --no-cache

# Copy application files
COPY --chown=budget_user:budget_group bot/ ./bot/
COPY --chown=budget_user:budget_group scripts/ ./scripts/
COPY --chown=budget_user:budget_group main.py ./main.py

# Set entry point
ENTRYPOINT ["python", "main.py"]
