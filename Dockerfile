# Base stage for Python dependencies
FROM python:3.9-slim AS python-base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV DB_TYPE=postgres

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Node.js stage for React build
FROM node:18-slim AS node-builder

WORKDIR /app/frontend/solport
COPY frontend/solport/package*.json ./
RUN npm ci
COPY frontend/solport/ ./
RUN npm run build

# Final stage
FROM python-base AS final

COPY . .
COPY --from=node-builder /app/frontend/solport/build /app/frontend/solport/build

RUN mkdir -p logs
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app

# Create entrypoint script
RUN echo '#!/bin/bash\n\
cd /app\n\
PORT_VALUE=${PORT:-8000}\n\
echo "Starting server on port $PORT_VALUE"\n\
exec gunicorn "app:create_app().app" --bind "0.0.0.0:$PORT_VALUE" --workers 4 --threads 2 --timeout 120\n\
' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

USER appuser

# Use the entrypoint script
CMD ["/app/entrypoint.sh"]