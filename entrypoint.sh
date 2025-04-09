#!/bin/bash

# Set the default port if PORT is not provided
PORT=${PORT:-5000}

# Print debug information
echo "Starting Gunicorn with PORT=$PORT"
echo "Current directory: $(pwd)"
echo "Files in current directory: $(ls -la)"

# Run Gunicorn with the specified port and arguments
exec gunicorn wsgi:app \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --timeout 120