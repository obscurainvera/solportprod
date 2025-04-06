from config.Config import get_config
from flask import Blueprint, render_template

reports_page_bp = Blueprint('reports_page', __name__)

@reports_page_bp.route('/reports')
def reports_page():
    """Render the reports page"""
    return render_template('reports.html') 