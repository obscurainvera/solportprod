from dotenv import load_dotenv
import os
import argparse

# Load environment variables from .env file
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run the portfolio monitoring application')
parser.add_argument('--port', type=int, help='Port to run the application on')
args = parser.parse_args()

from config.Config import get_config
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import time
import signal
import threading
import os
from sqlalchemy import create_engine, text
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from database.attention.AttentionHandler import AttentionHandler
from database.auth.CredentialsHandler import CredentialsHandler
from database.auth.TokenHandler import TokenHandler
from database.job.job_handler import JobHandler
from database.notification.NotificationHandler import NotificationHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from database.portsummary.PortfolioHandler import PortfolioHandler
from database.pumpfun.PumpfunHandler import PumpFunHandler
from database.smartmoneywallets.SMWalletTopPNLTokenHandler import SMWalletTopPNLTokenHandler
from database.smartmoneywallets.SmartMoneyPerformanceReportHandler import SmartMoneyPerformanceReportHandler
from database.smartmoneywallets.SmartMoneyWalletsHandler import SmartMoneyWalletsHandler
from database.smwalletsbehaviour.SmartMoneyWalletBehaviourHandler import SmartMoneyWalletBehaviourHandler
from database.volume.VolumeHandler import VolumeHandler
from database.walletinvested.WalletsInvestedHandler import WalletsInvestedHandler
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from logs.logger import get_logger
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
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
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
from sqlalchemy.engine.url import URL
import psycopg2
from psycopg2.extras import RealDictCursor
from database.operations.PortfolioDB import PortfolioDB

logger = get_logger(__name__)

from scheduler.JobRunner import JobRunner

logger = get_logger(__name__)

def initialize_job_storage():
    """Initialize job storage and required tables"""
    try:
        # We need to create a database engine to interact with the jobs database, 
        # which stores information about scheduled jobs. This engine is used to 
        # create the necessary tables for job storage.
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
    Initialize all database tables by creating an instance of PortfolioDB.
    PortfolioDB's constructor will initialize all database handlers,
    which in turn will create their respective tables.
    """
    try:
        logger.info("Initializing all database tables...")
        
        # Initialize handlers one by one to identify which one has the issue    
        conn_manager = DatabaseConnectionManager()
        
        # Dictionary to track initialization status
        init_status = {}
        
        # Initialize each handler individually to isolate errors
        try:
            logger.info("Initializing PortfolioHandler...")
            PortfolioHandler(conn_manager)
            init_status['PortfolioHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing PortfolioHandler: {e}")
            init_status['PortfolioHandler'] = f"Failed: {str(e)}"
        
        try:
            logger.info("Initializing WalletsInvestedHandler...")
            WalletsInvestedHandler(conn_manager)
            init_status['WalletsInvestedHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing WalletsInvestedHandler: {e}")
            init_status['WalletsInvestedHandler'] = f"Failed: {str(e)}"
        
        try:        
            logger.info("Initializing JobHandler...")
            JobHandler(conn_manager)
            init_status['JobHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing JobHandler: {e}")
            init_status['JobHandler'] = f"Failed: {str(e)}"
        
        try:    
            logger.info("Initializing SmartMoneyWalletsHandler...")
            SmartMoneyWalletsHandler(conn_manager)
            init_status['SmartMoneyWalletsHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing SmartMoneyWalletsHandler: {e}")
            init_status['SmartMoneyWalletsHandler'] = f"Failed: {str(e)}"
            
        try:
            logger.info("Initializing SMWalletTopPNLTokenHandler...")
            SMWalletTopPNLTokenHandler(conn_manager)
            init_status['SMWalletTopPNLTokenHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing SMWalletTopPNLTokenHandler: {e}")
            init_status['SMWalletTopPNLTokenHandler'] = f"Failed: {str(e)}"
            
        try:
            logger.info("Initializing SmartMoneyPerformanceReportHandler...")
            SmartMoneyPerformanceReportHandler(conn_manager)
            init_status['SmartMoneyPerformanceReportHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing SmartMoneyPerformanceReportHandler: {e}")
            init_status['SmartMoneyPerformanceReportHandler'] = f"Failed: {str(e)}"
            
        try:
            logger.info("Initializing AttentionHandler...")
            AttentionHandler(conn_manager)
            init_status['AttentionHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing AttentionHandler: {e}")
            init_status['AttentionHandler'] = f"Failed: {str(e)}"
            
        try:
            logger.info("Initializing VolumeHandler...")
            VolumeHandler(conn_manager)
            init_status['VolumeHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing VolumeHandler: {e}")
            init_status['VolumeHandler'] = f"Failed: {str(e)}"
            
        try:    
            logger.info("Initializing PumpFunHandler...")
            PumpFunHandler(conn_manager)
            init_status['PumpFunHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing PumpFunHandler: {e}")
            init_status['PumpFunHandler'] = f"Failed: {str(e)}"
            
        try:
            logger.info("Initializing TokenHandler...")
            TokenHandler(conn_manager)
            init_status['TokenHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing TokenHandler: {e}")
            init_status['TokenHandler'] = f"Failed: {str(e)}"
            
        try:
            logger.info("Initializing CredentialsHandler...")
            CredentialsHandler(conn_manager)
            init_status['CredentialsHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing CredentialsHandler: {e}")
            init_status['CredentialsHandler'] = f"Failed: {str(e)}"
            
        try:
            logger.info("Initializing AnalyticsHandler...")
            AnalyticsHandler(conn_manager)
            init_status['AnalyticsHandler'] = "Success" 
        except Exception as e:
            logger.error(f"Error initializing AnalyticsHandler: {e}")
            init_status['AnalyticsHandler'] = f"Failed: {str(e)}"
            
        try:
            logger.info("Initializing NotificationHandler...")
            NotificationHandler(conn_manager)
            init_status['NotificationHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing NotificationHandler: {e}")
            init_status['NotificationHandler'] = f"Failed: {str(e)}"
            
        try:    
            logger.info("Initializing SmartMoneyWalletBehaviourHandler...")
            SmartMoneyWalletBehaviourHandler(conn_manager)
            init_status['SmartMoneyWalletBehaviourHandler'] = "Success"
        except Exception as e:
            logger.error(f"Error initializing SmartMoneyWalletBehaviourHandler: {e}")
            init_status['SmartMoneyWalletBehaviourHandler'] = f"Failed: {str(e)}"
        
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
    Main application class that manages the Flask web server and background jobs.
    Handles graceful startup/shutdown and provides health monitoring endpoints.
    """
    
    def __init__(self):
        """
        Initialize core components:
        - Flask web server
        - Background job scheduler
        - Shutdown flag for graceful termination
        """
        logger.info("Initializing Portfolio App...")
        self.app = Flask(__name__, 
                         static_folder='frontend/solport/build/static',
                         template_folder='frontend/solport/build')
        
        # Configure CORS
        CORS(self.app, resources={r"/api/*": {"origins": "*"}})
        
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
        
        # Register API blueprints
        self.app.register_blueprint(wallets_invested_bp)
        self.app.register_blueprint(wallets_invested_investement_details_bp)
        self.app.register_blueprint(portfolio_bp)
        self.app.register_blueprint(health_bp)
        self.app.register_blueprint(dashboard_bp)
        self.app.register_blueprint(analytics_bp)
        self.app.register_blueprint(smart_money_wallets_bp)
        self.app.register_blueprint(smwallet_top_pnl_token_bp)
        self.app.register_blueprint(smwallet_top_pnl_token_investment_bp)
        self.app.register_blueprint(smartMoneyWalletsReportBp)
        self.app.register_blueprint(attention_bp)
        self.app.register_blueprint(volumebot_bp)
        self.app.register_blueprint(pumpfun_bp)
        self.app.register_blueprint(scheduler_bp)
        self.app.register_blueprint(portfolio_tagger_bp)
        self.app.register_blueprint(strategy_bp)
        self.app.register_blueprint(push_token_bp)
        self.app.register_blueprint(strategy_page_bp)
        self.app.register_blueprint(execution_monitor_bp)
        self.app.register_blueprint(smartMoneyWalletBehaviourBp)
        self.app.register_blueprint(reports_page_bp)
        self.app.register_blueprint(port_summary_report_bp)
        self.app.register_blueprint(smartMoneyPerformanceReportBp)
        self.app.register_blueprint(strategy_report_bp)
        self.app.register_blueprint(smwallet_investment_range_report_bp)
        self.app.register_blueprint(smwalletBehaviourReportBp)
        self.app.register_blueprint(strategyperformance_bp)
        self.app.register_blueprint(portfolio_allocation_bp)
        self.app.register_blueprint(attention_report_bp)
        self.app.register_blueprint(dexscrenner_bp)
        
        # Add before_request handler to ensure connection pool is available
        @self.app.before_request
        def ensure_db_connection():
            """Ensure database connection pool is available before each request"""
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
        
        # Add a dedicated healthcheck endpoint for container orchestration
        @self.app.route('/healthcheck', methods=['GET'])
        def healthcheck():
            """Simple health check endpoint for container orchestration systems"""
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
        
        logger.info("Portfolio app initialized successfully")

    def _setup_signal_handlers(self):
        """
        Configure system signal handlers (Ctrl+C, kill, etc.)
        Ensures graceful shutdown when the application is terminated
        """
        def handle_signal(signum, frame):
            if not self.is_shutting_down.is_set():
                logger.info(f"\n🛑 Received shutdown signal {signum}")
                self.shutdown()
                os._exit(0)  # Force exit to avoid threading issues

        signal.signal(signal.SIGINT, handle_signal)   # Handle Ctrl+C
        signal.signal(signal.SIGTERM, handle_signal)  # Handle kill command
        logger.info("✅ Signal handlers configured")

    def shutdown(self):
        """
        Graceful shutdown sequence:
        1. Set shutdown flag to prevent new operations
        2. Stop background job scheduler
        3. Close database connections
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

    def run(self):
        """
        Start the application:
        1. Setup signal handlers for graceful shutdown
        2. Start background jobs
        3. Launch Flask web server
        """
        config_instance = get_config()
        
        # Get port from command line args, env var, or config
        port = args.port if args.port else int(os.getenv('API_PORT', config_instance.API_PORT))
        host = config_instance.API_HOST
        
        try:
            self._setup_signal_handlers()
            self.job_runner.start()
            logger.info("✅ Background jobs started")
            
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
    """Factory function for creating application instance"""
    return PortfolioApp()

if __name__ == '__main__':
    app = create_app()
    app.run()
