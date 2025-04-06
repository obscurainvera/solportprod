from config.Config import get_config
from flask import Blueprint, render_template

strategy_page_bp = Blueprint('strategy_page', __name__)

@strategy_page_bp.route('/strategy')
def strategy_page():
    """Render the strategy analytics page"""
    return render_template('strategy.html') 