from config.Config import get_config
from flask import Blueprint, render_template

# Create Blueprint for dashboard
dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')

@dashboard_bp.route('/dashboard')
def dashboard():
    """Render the dashboard UI"""
    return render_template('dashboard.html') 