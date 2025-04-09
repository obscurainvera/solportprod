#!/bin/bash

PORT=${PORT:-10000}
echo "Starting Waitress on port $PORT"
/usr/local/bin/waitress-serve --listen=0.0.0.0:$PORT wsgi:app