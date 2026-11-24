# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for psycopg2 and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install requirements to user directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final Runner
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime libraries (like libpq for PostgreSQL connection)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source code
COPY app/ ./app/

COPY . .
RUN chmod +x /app/entrypoint.sh

ENV DB_FILE=/app/expenses.db \
    BLOB_CONTAINER=dbcontainer \
    BLOB_NAME=expenses.db

# Expose default HTTP port
EXPOSE 8000

# Set environment defaults
ENV PORT=8000
ENV ENV=production
ENV DATABASE_URL=""

ENTRYPOINT ["/app/entrypoint.sh"]
# Start the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
