"""
WSGI entry point for the Portfolio Monitoring System.

This module creates and runs the Flask application defined in app.py without
using Gunicorn or Waitress. It uses Flask's built-in server for simplicity,
configured to serve both the API and the React frontend.
"""

import os
from app import create_app  # Import the factory function from app.py

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Get port from environment variable (set by Docker) or default to 5000
    port = int(os.getenv('PORT', 5000))
    host = "0.0.0.0"  # Bind to all interfaces for Docker

    # Run the Flask app directly
    app.run()