"""
Portfolio Monitoring System - Main Application Module

This module serves as the entry point for the Flask-based Portfolio Monitoring System.
It provides a web server with RESTful API endpoints, background job scheduling, and
database interactions for portfolio analytics, smart money tracking, and investment monitoring.
"""

from dotenv import load_dotenv
import os
import argparse
import time
import signal
import threading
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Run the portfolio monitoring application')
parser.add_argument('--port', type=int, help='Port to run the application on')
args = parser.parse_args()

# Local module imports
from config.Config import get_config
from logs.logger import get_logger
from scheduler.JobRunner import JobRunner
from database.operations.PortfolioDB import PortfolioDB
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager

# Handler imports
from database.attention.AttentionHandler import AttentionHandler
from database.auth.CredentialsHandler import CredentialsHandler
from database.auth.TokenHandler import TokenHandler
from database.job.job_handler import JobHandler
from database.notification.NotificationHandler import NotificationHandler
from database.portsummary.PortfolioHandler import PortfolioHandler
from database.pumpfun.PumpfunHandler import PumpFunHandler
from database.smartmoneywallets.SMWalletTopPNLTokenHandler import SMWalletTopPNLTokenHandler
from database.smartmoneywallets.SmartMoneyPerformanceReportHandler import SmartMoneyPerformanceReportHandler
from database.smartmoneywallets.SmartMoneyWalletsHandler import SmartMoneyWalletsHandler
from database.smwalletsbehaviour.SmartMoneyWalletBehaviourHandler import SmartMoneyWalletBehaviourHandler
from database.volume.VolumeHandler import VolumeHandler
from database.walletinvested.WalletsInvestedHandler import WalletsInvestedHandler
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler

# Blueprint imports
from api.walletsinvested.WalletsInvestedAPI import wallets_invested_bp
from api.walletsinvested.WalletsInvestedInvestmentDetailsAPI import wallets_invested_investement_details_bp
from api.portsummary.PortfolioAPI import portfolio_bp
from api.operations.HealthAPI import health_bp
from api.operations.DashboardAPI import dashboard_bp
from api.operations.AnalyticsAPI import analytics_bp
from api.smartmoney.SmartMoneyWalletsAPI import smart_money_wallets_bp
from api.smartmoney.SMWalletTopPNLTokenAPI import smwallet_top_pnl_token_bp
from api.smartmoney.SMWalletTopPNLTokenInvestmentAPI import smwallet_top_pnl_token_investment_bp
from api.attention.AttentionAPI import attention_bp
from api.volume.VolumebotAPI import volumebot_bp
from api.pumpfun.PumpfunAPI import pumpfun_bp  
from api.operations.SchedulerAPI import scheduler_bp
from api.portsummary.PortfolioTaggerAPI import portfolio_tagger_bp
from api.analyticsframework.CreateStrategyAPI import strategy_bp
from api.analyticsframework.PushTokenFrameworkAPI import push_token_bp
from api.operations.StrategyAPI import strategy_page_bp
from api.analyticsframework.ExecutionMonitorAPI import execution_monitor_bp
from api.smartmoneywalletsbehaviour.SmartMoneyWalletsBehaviourAPI import smartMoneyWalletBehaviourBp
from api.operations.ReportsAPI import reports_page_bp
from api.portsummary.PortSummaryReportAPI import port_summary_report_bp
from api.smartmoney.SmartMoneyWalletsReportAPI import smartMoneyWalletsReportBp
from api.smartmoney.SmartMoneyPerformanceReportAPI import smartMoneyPerformanceReportBp
from api.strategyreport.StrategyReportAPI import strategy_report_bp
from api.strategyreport.StrategyPerformanceAPI import strategyperformance_bp
from api.smwalletsbehaviour.SMWalletBehaviourReportAPI import smwalletBehaviourReportBp
from api.smwalletsbehaviour.SMWalletInvestmentRangeReportAPI import smwallet_investment_range_report_bp
from api.portfolioallocation.PortfolioAllocationAPI import portfolio_allocation_bp
from api.attention.AttentionReportAPI import attention_report_bp
from api.dexscrenner.DexScrennerAPI import dexscrenner_bp

logger = get_logger(__name__)

def initialize_database():
    """
    Initialize all database tables for job tracking and application data in a centralized manner.
    
    Creates:
    - Job tracking tables: `job_locks`, `job_executions`
    - Application-specific tables via handlers
    """
    config_instance = get_config()
    try:
        # Initialize job tracking tables
        conn = psycopg2.connect(
            user=config_instance.DB_USER,
            password=config_instance.DB_PASSWORD,
            host=config_instance.DB_HOST,
            port=config_instance.DB_PORT,
            dbname=config_instance.DB_NAME,
            sslmode=config_instance.DB_SSLMODE,
            gssencmode=config_instance.DB_GSSENCMODE
        )
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS job_locks (
                    job_id TEXT PRIMARY KEY,
                    locked_at TIMESTAMP NOT NULL,
                    timeout INTEGER NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS job_executions (
                    id SERIAL PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        conn.close()
        logger.info("Job storage tables initialized successfully")

        # Initialize application-specific tables
        conn_manager = DatabaseConnectionManager()
        handlers = {
            'PortfolioHandler': PortfolioHandler,
            'WalletsInvestedHandler': WalletsInvestedHandler,
            'JobHandler': JobHandler,
            'SmartMoneyWalletsHandler': SmartMoneyWalletsHandler,
            'SMWalletTopPNLTokenHandler': SMWalletTopPNLTokenHandler,
            'SmartMoneyPerformanceReportHandler': SmartMoneyPerformanceReportHandler,
            'AttentionHandler': AttentionHandler,
            'VolumeHandler': VolumeHandler,
            'PumpFunHandler': PumpFunHandler,
            'TokenHandler': TokenHandler,
            'CredentialsHandler': CredentialsHandler,
            'AnalyticsHandler': AnalyticsHandler,
            'NotificationHandler': NotificationHandler,
            'SmartMoneyWalletBehaviourHandler': SmartMoneyWalletBehaviourHandler
        }
        for name, handler_class in handlers.items():
            try:
                handler_class(conn_manager)
                logger.info(f"{name} initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Continuing with limited functionality")

class PortfolioApp:
    """
    Core class managing the Flask application, scheduler, and database interactions.
    
    Responsibilities:
    - Initialize Flask app and API endpoints
    - Manage background job scheduling
    - Handle database setup and connections
    - Ensure graceful shutdown
    """
    def __init__(self):
        """Initialize the Flask app, database, scheduler, and API routes."""
        logger.info("Initializing PortfolioApp...")
        self.app = Flask(__name__, 
                        static_folder='frontend/solport/build',
                        template_folder='frontend/solport/build')
        
        # Configure CORS
        allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
        origins = allowed_origins.split(',') if allowed_origins != '*' else '*'
        CORS(self.app, resources={r"/api/*": {"origins": origins}})

        # Setup database and scheduler
        initialize_database()
        self.job_runner = JobRunner() if self._init_job_runner() else None
        self.is_shutting_down = threading.Event()

        # Register routes and handlers
        self._register_blueprints()
        self._setup_request_handlers()
        self._setup_healthcheck()
        logger.info("PortfolioApp initialized successfully")

    def _init_job_runner(self) -> bool:
        """Initialize the JobRunner with error handling."""
        try:
            return True
        except Exception as e:
            logger.error(f"Failed to initialize JobRunner: {e}")
            logger.warning("Running without scheduler")
            return False

    def _register_blueprints(self):
        """Register all API blueprints for modular route management."""
        blueprints = [
            wallets_invested_bp, wallets_invested_investement_details_bp, portfolio_bp,
            health_bp, dashboard_bp, analytics_bp, smart_money_wallets_bp,
            smwallet_top_pnl_token_bp, smwallet_top_pnl_token_investment_bp, attention_bp,
            volumebot_bp, pumpfun_bp, scheduler_bp, portfolio_tagger_bp, strategy_bp,
            push_token_bp, strategy_page_bp, execution_monitor_bp, smartMoneyWalletBehaviourBp,
            reports_page_bp, port_summary_report_bp, smartMoneyWalletsReportBp,
            smartMoneyPerformanceReportBp, strategy_report_bp, strategyperformance_bp,
            smwalletBehaviourReportBp, smwallet_investment_range_report_bp, portfolio_allocation_bp,
            attention_report_bp, dexscrenner_bp
        ]
        for bp in blueprints:
            self.app.register_blueprint(bp)

    def _setup_request_handlers(self):
        """Configure request middleware for database connection management."""
        @self.app.before_request
        def ensure_db_connection():
            """Ensure database connection pool is active before each request."""
            conn_manager = DatabaseConnectionManager()
            if conn_manager.is_pool_closed():
                logger.warning("Reinitializing closed connection pool")
                conn_manager.reinitialize_pool_if_closed()

    def _setup_healthcheck(self):
        """Add healthcheck endpoint for system monitoring."""
        @self.app.route('/healthcheck', methods=['GET'])
        def healthcheck():
            """Return system health status."""
            try:
                PortfolioDB().check_connection()
                return jsonify({
                    'status': 'healthy',
                    'timestamp': time.time(),
                    'database': 'connected',
                    'scheduler': 'running' if self.job_runner else 'disabled'
                }), 200
            except Exception as e:
                logger.error(f"Healthcheck failed: {e}")
                return jsonify({
                    'status': 'degraded',
                    'error': str(e),
                    'scheduler': 'disabled' if not self.job_runner else 'unknown'
                }), 200

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def handle_signal(signum, _):
            if not self.is_shutting_down.is_set():
                logger.info(f"Received signal {signum}, shutting down...")
                self.shutdown()
                os._exit(0)
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        logger.info("Signal handlers configured")

    def shutdown(self):
        """Gracefully shut down the application."""
        if not self.is_shutting_down.is_set():
            self.is_shutting_down.set()
            if self.job_runner:
                self.job_runner.shutdown()
                logger.info("Job runner stopped")
            PortfolioDB().close()
            logger.info("Database connections closed")

    def run(self, host=None, port=None):
        """Run the Flask application with scheduler and signal handling."""
        config = get_config()
        host = host or config.API_HOST
        port = port or args.port or config.API_PORT
        self._setup_signal_handlers()
        if self.job_runner:
            self.job_runner.start()
            logger.info("Background jobs started")
        else:
            logger.warning("No background jobs running")
        logger.info(f"Starting server at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

def create_app():
    """Factory function to create and configure the PortfolioApp instance."""
    app = PortfolioApp()
    
    @app.app.route('/', defaults={'path': ''})
    @app.app.route('/<path:path>')
    def serve_react(path):
        """Serve React frontend with client-side routing support."""
        static_folder = app.app.static_folder
        if path and os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run()