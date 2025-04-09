#!/bin/bash

PORT=${PORT:-10000}
echo "Starting Waitress on port $PORT"
exec waitress-serve --host=0.0.0.0 --port=$PORT wsgi:app