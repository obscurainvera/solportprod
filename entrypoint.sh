#!/bin/bash

PORT=${PORT:-10000}
echo "Starting Flask on port $PORT"
exec python wsgi.py --host=0.0.0.0 --port=$PORT