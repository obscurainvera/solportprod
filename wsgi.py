from app import create_app

# Create the Flask application instance
portfolio_app = create_app()
# The 'app' variable is what Gunicorn will look for
app = portfolio_app.app 