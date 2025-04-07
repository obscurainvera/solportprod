# Base stage for Python dependencies
FROM python:3.9-slim AS python-base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV DB_TYPE=postgres

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Node.js stage for React build
FROM node:18-slim AS node-builder

# Set working directory
WORKDIR /app/frontend/solport

# Copy package.json and package-lock.json
COPY frontend/solport/package*.json ./

# Install dependencies
RUN npm ci

# Copy React source code
COPY frontend/solport/ ./

# Build React application
RUN npm run build

# Final stage
FROM python-base AS final

# Copy Python application
COPY . .

# Copy React build from node-builder stage
COPY --from=node-builder /app/frontend/solport/build /app/frontend/solport/build

# Create necessary directories
RUN mkdir -p logs

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/healthcheck || exit 1

# Expose port
EXPOSE 8080

# Run the application with gunicorn for production
CMD gunicorn --bind=0.0.0.0:8080 --workers=4 --threads=2 --timeout=120 wsgi:app 