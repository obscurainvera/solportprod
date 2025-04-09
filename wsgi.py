"""
WSGI entry point for the Portfolio Monitoring System.

This module creates and runs the Flask application defined in app.py without
using Gunicorn or Waitress. It uses Flask's built-in server for simplicity,
configured to serve both the API and the React frontend.
"""

import os
import argparse
from app import create_app  # Import the factory function from app.py

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Portfolio Monitoring System')
    parser.add_argument('--port', type=int, help='Port to run the application on')
    parser.add_argument('--host', type=str, help='Host to bind the application to')
    args = parser.parse_args()
    
    # Get port from command line args, environment variable, or default to 5000
    port = args.port if args.port else int(os.getenv('PORT', 10000))
    # Get host from command line args or default to 0.0.0.0 for Docker
    host = args.host if args.host else "0.0.0.0"

    # Run the Flask app directly
    app.run(host=host,port=port)