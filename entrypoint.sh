#!/bin/bash

PORT=${PORT:-5000}
echo "Starting Flask on port $PORT"
exec python wsgi.py --host=0.0.0.0 --port=$PORT