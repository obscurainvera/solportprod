#!/bin/bash

# Set default port if not provided
PORT="${PORT:-8000}"

# Print startup message
echo "Starting gunicorn server on port $PORT"

# Execute gunicorn with proper parameters
exec gunicorn "app:create_app().app" \
    --bind "0.0.0.0:$PORT" \
    --workers 4 \
    --threads 2 \
    --timeout 120 