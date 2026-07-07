#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Run whatever command was passed to the container
echo "Starting: $@"
exec "$@"