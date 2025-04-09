#!/bin/bash

PORT=${PORT:-10000}
echo "Starting Flask on port $PORT"
exec python wsgi.py --port=$PORT