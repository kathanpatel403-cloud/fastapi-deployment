#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start uvicorn server
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
