#!/bin/sh

# Set the default port if PORT is not provided
PORT=${PORT:-5000}

# Run Gunicorn with the specified port and arguments
exec gunicorn -b 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 wsgi:app