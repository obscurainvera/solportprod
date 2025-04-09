#!/bin/sh

# Set the default port if PORT is not provided
PORT=${PORT:-5000}

# Run Gunicorn with the specified port and arguments
exec gunicorn wsgi:app -b 0.0.0.0:$PORT -w 4 -t 120