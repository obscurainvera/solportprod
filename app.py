"""
Portfolio Monitoring System - Main Application Module

This module serves as the entry point for the Portfolio Monitoring System application.
It provides a Flask web server with RESTful API endpoints and background job scheduling
for portfolio analytics, smart money tracking, and investment monitoring.

The application architecture includes:
- Database connection management and ORM integration
- RESTful API with various endpoints for portfolio data
- Background job scheduling for periodic tasks
- Frontend integration with React
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
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# Load environment variables from .env file
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run the portfolio monitoring application')
parser.add_argument('--port', type=int, help='Port to run the application on')
args = parser.parse_args()

# Import local modules after environment setup
from config.Config import get_config
from logs.logger import get_logger
from scheduler.JobRunner import JobRunner
from database.operations.PortfolioDB import PortfolioDB
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager

# Import all necessary handlers
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
from framework.analyticsframework.enums.SourceTypeEnum import SourceType

# Import all API blueprints
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

def initialize_job_storage():
    """
    Initialize job storage database tables for scheduled job tracking.
    
    Creates necessary tables for APScheduler including job_locks and job_executions
    to track job status, execution history, and prevent duplicate executions.
    Falls back to memory-based storage if database initialization fails.
    """
    try:
        config_instance = get_config()
        
        try:
            # Create direct connection to PostgreSQL
            conn = psycopg2.connect(
                user=config_instance.DB_USER,
                password=config_instance.DB_PASSWORD,
                host=config_instance.DB_HOST,
                port=config_instance.DB_PORT,
                dbname=config_instance.DB_NAME,
                sslmode=config_instance.DB_SSLMODE,
                gssencmode=config_instance.DB_GSSENCMODE
            )
            
            # Create tables with psycopg2
            with conn.cursor() as cur:
                # Create job_locks table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS job_locks (
                        job_id TEXT PRIMARY KEY,
                        locked_at TIMESTAMP NOT NULL,
                        timeout INTEGER NOT NULL
                    )
                """)
                
                # Create job_executions table with PostgreSQL syntax
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
            logger.info("Job storage initialized successfully using psycopg2")
            
        except psycopg2.Error as pg_error:
            logger.error(f"PostgreSQL error: {pg_error}")
            logger.warning("Application will continue with memory-based job storage")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL with psycopg2: {e}")
            logger.warning("Application will continue with memory-based job storage")
            raise
    except Exception as e:
        logger.error(f"Failed to initialize job storage: {e}")
        logger.warning("Application will continue with memory-based job storage")
        # Don't raise the exception - let the application continue with in-memory storage

def initialize_all_tables():
    """
    Initialize all database tables required by the application.
    
    Creates all required database tables by initializing handler objects,
    each responsible for their own table schema. This approach follows
    the single responsibility principle and provides isolated error handling
    for each database component.
    """
    try:
        logger.info("Initializing all database tables...")
        
        # Initialize handlers one by one to identify which one has the issue    
        conn_manager = DatabaseConnectionManager()
        
        # Dictionary to track initialization status
        init_status = {}
        
        # Initialize each handler individually to isolate errors
        handlers_to_init = {
            'PortfolioHandler': lambda: PortfolioHandler(conn_manager),
            'WalletsInvestedHandler': lambda: WalletsInvestedHandler(conn_manager),
            'JobHandler': lambda: JobHandler(conn_manager),
            'SmartMoneyWalletsHandler': lambda: SmartMoneyWalletsHandler(conn_manager),
            'SMWalletTopPNLTokenHandler': lambda: SMWalletTopPNLTokenHandler(conn_manager),
            'SmartMoneyPerformanceReportHandler': lambda: SmartMoneyPerformanceReportHandler(conn_manager),
            'AttentionHandler': lambda: AttentionHandler(conn_manager),
            'VolumeHandler': lambda: VolumeHandler(conn_manager),
            'PumpFunHandler': lambda: PumpFunHandler(conn_manager),
            'TokenHandler': lambda: TokenHandler(conn_manager),
            'CredentialsHandler': lambda: CredentialsHandler(conn_manager),
            'AnalyticsHandler': lambda: AnalyticsHandler(conn_manager),
            'NotificationHandler': lambda: NotificationHandler(conn_manager),
            'SmartMoneyWalletBehaviourHandler': lambda: SmartMoneyWalletBehaviourHandler(conn_manager)
        }
        
        # Initialize each handler with proper error handling
        for handler_name, init_func in handlers_to_init.items():
            try:
                logger.info(f"Initializing {handler_name}...")
                init_func()
                init_status[handler_name] = "Success"
            except Exception as e:
                logger.error(f"Error initializing {handler_name}: {e}")
                init_status[handler_name] = f"Failed: {str(e)}"
        
        # Summary of initialization status
        success_count = sum(1 for status in init_status.values() if status == "Success")
        total_count = len(init_status)
        
        logger.info(f"Database initialization completed: {success_count}/{total_count} handlers successful")
        if success_count < total_count:
            logger.warning("Some handlers failed to initialize. Check the logs for details.")
        else:
            logger.info("All database tables initialized successfully")
            
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        # Don't raise the exception, allow the app to continue

class PortfolioApp:
    """
    Main application class for the Portfolio Monitoring System.
    
    This class manages the core components of the application:
    1. Flask web server with RESTful API endpoints
    2. Background job scheduler for periodic tasks
    3. Database connection management
    4. Signal handling for graceful shutdown
    
    The application follows a modular design pattern with:
    - Database handlers for different data domains
    - API blueprints for route organization
    - Background job scheduler for async processing
    - Frontend integration via React
    """
    
    def __init__(self):
        """
        Initialize the Portfolio App with all required components.
        
        Sets up:
        - Flask web server with CORS configuration
        - Database tables and connections
        - Background job scheduler
        - API blueprints for different endpoints
        - Request middleware for connection management
        """
        logger.info("Initializing Portfolio App...")
        self.app = Flask(__name__, 
                         static_folder='frontend/solport/build',
                         template_folder='frontend/solport/build')
        
        # Configure CORS for production
        # Get allowed origins from environment variable, fall back to * in development
        allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
        origins = [origin.strip() for origin in allowed_origins.split(',')] if allowed_origins != '*' else '*'
        CORS(self.app, resources={r"/api/*": {"origins": origins}})
        
        # Initialize components with graceful error handling
        initialize_job_storage()  # This now handles its own errors
        initialize_all_tables()   # Initialize all database tables

        try:
            self.job_runner = JobRunner()
        except Exception as e:
            logger.error(f"Failed to initialize JobRunner: {e}")
            logger.warning("Continuing without job scheduler - scheduled tasks will not run")
            self.job_runner = None  # We'll check for this later before using it
        
        self.is_shutting_down = threading.Event()
        
        # Register all API blueprints
        self._register_blueprints()
        
        # Add before_request handler to ensure connection pool is available
        self._setup_request_handlers()
        
        # Add healthcheck endpoint
        self._setup_healthcheck()
        
        logger.info("Portfolio app initialized successfully")

    def _register_blueprints(self):
        """
        Register all API blueprints with the Flask application.
        
        Organizes routes into logical groups by functionality area.
        """
        blueprints = [
            wallets_invested_bp,
            wallets_invested_investement_details_bp,
            portfolio_bp,
            health_bp,
            dashboard_bp,
            analytics_bp,
            smart_money_wallets_bp,
            smwallet_top_pnl_token_bp,
            smwallet_top_pnl_token_investment_bp,
            smartMoneyWalletsReportBp,
            attention_bp,
            volumebot_bp,
            pumpfun_bp,
            scheduler_bp,
            portfolio_tagger_bp,
            strategy_bp,
            push_token_bp,
            strategy_page_bp,
            execution_monitor_bp,
            smartMoneyWalletBehaviourBp,
            reports_page_bp,
            port_summary_report_bp,
            smartMoneyPerformanceReportBp,
            strategy_report_bp,
            smwallet_investment_range_report_bp,
            smwalletBehaviourReportBp,
            strategyperformance_bp,
            portfolio_allocation_bp,
            attention_report_bp,
            dexscrenner_bp
        ]
        
        for blueprint in blueprints:
            self.app.register_blueprint(blueprint)

    def _setup_request_handlers(self):
        """
        Setup Flask request handlers for middleware functionality.
        
        Adds hooks for:
        - Database connection management
        - Request preprocessing
        """
        @self.app.before_request
        def ensure_db_connection():
            """
            Ensure database connection pool is available before processing each request.
            
            Checks connection status and reinitializes if needed.
            """
            try:
                # Get a singleton instance of the connection manager
                conn_manager = DatabaseConnectionManager()
                
                # Check if pool is closed and reinitialize if needed
                if conn_manager.is_pool_closed():
                    logger.warning("Connection pool is closed before request, attempting to reinitialize")
                    conn_manager.reinitialize_pool_if_closed()
            except Exception as e:
                logger.error(f"Error checking database connection: {e}")
                # Don't fail the request - let it proceed and possibly
                # fail with a more specific error if it needs the database

    def _setup_healthcheck(self):
        """
        Setup health check endpoint for monitoring and orchestration systems.
        
        Provides system status information including database connectivity
        and scheduler status.
        """
        @self.app.route('/healthcheck', methods=['GET'])
        def healthcheck():
            """
            Simple health check endpoint for container orchestration systems.
            
            Returns a JSON response with system component status.
            """
            try:
                # Test database connection
                db = PortfolioDB()
                db.check_connection()
                
                scheduler_status = "running" if self.job_runner else "disabled"
                
                return jsonify({
                    'status': 'healthy',
                    'timestamp': time.time(),
                    'database': 'connected',
                    'database_type': get_config().DB_TYPE,
                    'scheduler': scheduler_status
                }), 200
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                return jsonify({
                    'status': 'degraded',
                    'timestamp': time.time(),
                    'error': str(e),
                    'scheduler': 'disabled' if not self.job_runner else 'unknown'
                }), 200  # Return 200 even for degraded state to keep container running

    def _setup_signal_handlers(self):
        """
        Configure system signal handlers for graceful shutdown.
        
        Handles SIGINT (Ctrl+C) and SIGTERM (kill command) to ensure proper
        cleanup of resources before termination.
        """
        def handle_signal(signum, frame):
            """
            Signal handler callback that initiates graceful shutdown.
            
            Args:
                signum: Signal number received
                frame: Current stack frame
            """
            if not self.is_shutting_down.is_set():
                logger.info(f"\n🛑 Received shutdown signal {signum}")
                self.shutdown()
                os._exit(0)  # Force exit to avoid threading issues

        signal.signal(signal.SIGINT, handle_signal)   # Handle Ctrl+C
        signal.signal(signal.SIGTERM, handle_signal)  # Handle kill command
        logger.info("✅ Signal handlers configured")

    def shutdown(self):
        """
        Perform graceful shutdown sequence for the application.
        
        Stops the job scheduler and closes database connections to ensure
        resources are released properly.
        """
        if not self.is_shutting_down.is_set():
            self.is_shutting_down.set()
            
            if self.job_runner:
                logger.info("Shutting down job runner...")
                self.job_runner.shutdown()
                logger.info("✅ Job runner stopped")
            else:
                logger.info("No job runner to shut down")

            try:
                logger.info("Closing database connections...")
                PortfolioDB().close()
                logger.info("✅ Database connections closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")

    def run(self, host=None, port=None):
        """
        Start the Portfolio Application with all components.
        
        Initializes signal handlers, starts background jobs, and launches
        the Flask web server.
        """
        config_instance = get_config()
        
        # Get port from command line args, env var, or config
        port = port if port else config_instance.API_PORT
        host = host if host else config_instance.API_HOST
        
        try:
            self._setup_signal_handlers()
            
            if self.job_runner:
                self.job_runner.start()
                logger.info("✅ Background jobs started")
            else:
                logger.warning("⚠️ Running without background job scheduler")
            
            logger.info("\n🚀 Starting Portfolio Monitoring System")
            logger.info(f"🔗 API available at http://{host}:{port}")
            
            self.app.run(
                host=host,
                port=port,
                debug=False,
                use_reloader=False,  # Prevent duplicate processes
                threaded=True        # Enable concurrent request handling
            )
            
        except Exception as e:
            logger.error(f"🔥 Critical startup error: {e}")
            self.shutdown()
            raise

def create_app():
    """
    Factory function for creating application instance.
    
    Follows Flask application factory pattern for better testability
    and modular configuration. Also sets up frontend routes for the
    React application.
    
    Returns:
        PortfolioApp: Configured application instance
    """
    portfolio_app = PortfolioApp()
    
    # Add a catch-all route to serve the React frontend for all non-API routes
    @portfolio_app.app.route('/', defaults={'path': ''})
    @portfolio_app.app.route('/<path:path>')
    def serve_react(path):
        """
        Serve the React app for any path not matched by API routes.
        
        Enables client-side routing support in the frontend application.
        
        Args:
            path: URL path component
            
        Returns:
            Flask response with appropriate content
        """
        if path != "" and os.path.exists(os.path.join(portfolio_app.app.static_folder, path)):
            # If requesting a static file that exists, serve it directly
            return send_from_directory(portfolio_app.app.static_folder, path)
        else:
            # Otherwise serve the index.html for client-side routing
            return render_template('index.html')
    
    return portfolio_app