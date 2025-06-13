## ------------------------------- Builder Stage ------------------------------ ##
FROM python:3.12-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

WORKDIR /app

# Copy the poetry configuration files
COPY backend/pyproject.toml backend/poetry.lock* ./

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.12-slim-bookworm AS production

# Install dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        curl supervisor && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a user for the application
RUN useradd --create-home appuser

# Create app directory with proper permissions
RUN mkdir -p /app && chown -R appuser:appuser /app

# Copy backend files
COPY backend/hexglobe /app/hexglobe/
COPY backend/run.py /app/

# Copy frontend files
COPY frontend /app/frontend/

# Copy mods directory
COPY mods /app/mods/

# Create empty data directory structure
RUN mkdir -p /app/data/static /app/data/dynamic /app/data/hex_maps && \
    chown -R appuser:appuser /app/data

# Create symbolic link from /data to /app/data for backend compatibility
RUN ln -sf /app/data /data

# Create supervisor configuration
RUN mkdir -p /etc/supervisor/conf.d
COPY hexglobe/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directory for supervisor
RUN mkdir -p /var/log/supervisor

# Set proper permissions for the application directories
RUN chown -R appuser:appuser /app

# Switch to appuser for application setup
USER appuser
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs

# Copy dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Expose ports for FastAPI and frontend
EXPOSE 8000 8080

# Start supervisord to manage both backend and frontend
USER root
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]