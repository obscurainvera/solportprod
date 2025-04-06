from config.Config import get_config
from flask import Blueprint, render_template
from framework.analyticsframework.enums.SourceTypeEnum import SourceType

# Create Blueprint for analytics
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')