from config.Config import get_config
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import time
import signal
import threading
import os
from sqlalchemy import create_engine, text
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
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

logger = get_logger(__name__)

from scheduler.JobRunner import JobRunner
from database.operations.PortfolioDB import PortfolioDB

logger = get_logger(__name__)

def initialize_job_storage():
    """Initialize job storage and required tables"""
    try:
        # We need to create a database engine to interact with the jobs database, 
        # which stores information about scheduled jobs. This engine is used to 
        # create the necessary tables for job storage.
        config_instance = get_config()
        if config_instance.DB_TYPE == 'sqlite':
            # Make sure the directory exists
            db_dir = os.path.dirname(os.path.abspath(config_instance.JOBS_DB_PATH))
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
            engine = create_engine(f'sqlite:///{config_instance.JOBS_DB_PATH}')
        else:
            # Use PostgreSQL for jobs database in production with explicit parameters
            
            postgres_url = URL.create(
                drivername="postgresql",
                username=config_instance.DB_USER,
                password=config_instance.DB_PASSWORD,
                host=config_instance.DB_HOST,
                port=config_instance.DB_PORT,
                database=config_instance.DB_NAME
            )

            logger.info(f"Using PostgreSQL URL: {postgres_url}")
            
            engine = create_engine(
                postgres_url,
                pool_size=config_instance.DB_POOL_SIZE,
                max_overflow=config_instance.DB_MAX_OVERFLOW,
                pool_timeout=config_instance.DB_POOL_TIMEOUT,
                pool_recycle=config_instance.DB_POOL_RECYCLE,
                pool_pre_ping=True
            )
        
        # Create monitoring tables with proper error handling
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS job_locks (
                        job_id TEXT PRIMARY KEY,
                        locked_at TIMESTAMP NOT NULL,
                        timeout INTEGER NOT NULL
                    )
                """))
                
                # Create job_executions table with DB-specific syntax
                if config_instance.DB_TYPE == 'sqlite':
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS job_executions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            job_id TEXT NOT NULL,
                            start_time TIMESTAMP NOT NULL,
                            end_time TIMESTAMP,
                            status TEXT NOT NULL,
                            error_message TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                else:
                    # PostgreSQL syntax
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS job_executions (
                            id SERIAL PRIMARY KEY,
                            job_id TEXT NOT NULL,
                            start_time TIMESTAMP NOT NULL,
                            end_time TIMESTAMP,
                            status TEXT NOT NULL,
                            error_message TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
            logger.info("Job storage initialized successfully")
        except Exception as table_error:
            logger.error(f"Failed to create job tables: {table_error}")
            # We can continue without these tables - they'll be handled by the memory-based scheduler
    except Exception as e:
        logger.error(f"Failed to initialize job storage: {e}")
        logger.warning("Application will continue with memory-based job storage")
        # Don't raise the exception - let the application continue with in-memory storage

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

    def run(self, host='0.0.0.0', port=8080):
        """
        Start the application:
        1. Setup signal handlers for graceful shutdown
        2. Start background jobs
        3. Launch Flask web server
        
        Args:
            host: Network interface to bind to
            port: Port number to listen on
        """
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
    port = int(os.environ.get('PORT', 8080))
    app = create_app()
    app.run(port=port)
