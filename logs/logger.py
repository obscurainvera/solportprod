from config.Config import get_config
import logging
import sys
from pathlib import Path
from datetime import datetime
import os
from logging.handlers import RotatingFileHandler

def get_logger(name: str) -> logging.Logger:
    """
    Get configured logger instance with multiple handlers for different purposes
    
    Args:
        name: Logger name (usually __name__ from the calling module)
        
    Returns:
        Configured logger instance
    """
    # Create logs directory relative to this file's location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    log_dir = os.path.join(project_root, 'logs')
    
    # Create directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Define log files
    date_suffix = datetime.now().strftime('%Y%m%d')
    
    # Main consolidated log file
    consolidated_log = os.path.join(log_dir, f"consolidated_{date_suffix}.log")
    
    # Action-specific log files
    action_logs = {
        'portfolio': os.path.join(log_dir, f"portfolio_{date_suffix}.log"),
        'walletsinvested': os.path.join(log_dir, f"wallets_invested_{date_suffix}.log"),
        'attention': os.path.join(log_dir, f"attention_{date_suffix}.log"),
        'transaction': os.path.join(log_dir, f"transaction_{date_suffix}.log"),
        'scheduler': os.path.join(log_dir, f"scheduler_{date_suffix}.log"),
        'parser': os.path.join(log_dir, f"parser_{date_suffix}.log"),
        'database': os.path.join(log_dir, f"database_{date_suffix}.log"),
        'api': os.path.join(log_dir, f"api_{date_suffix}.log"),
        'smwallettoppnltoken': os.path.join(log_dir, f"smwallet_top_pnl_token_{date_suffix}.log"),
        'smwallettoppnltokeninvestment': os.path.join(log_dir, f"smwallet_top_pnl_token_investment_{date_suffix}.log"),
        'volumebot': os.path.join(log_dir, f"volumebot_{date_suffix}.log"),
        'pumpfun': os.path.join(log_dir, f"pumpfun_{date_suffix}.log"),
        'dexscreener': os.path.join(log_dir, f"dexscreener_{date_suffix}.log"),
        'error': os.path.join(log_dir, f"error_{date_suffix}.log"),
        # Add new log files for analytics framework
        'analyticsframework': os.path.join(log_dir, f"analytics_framework_{date_suffix}.log"),
        'strategy': os.path.join(log_dir, f"strategy_{date_suffix}.log"),
        'pushtoken': os.path.join(log_dir, f"push_token_{date_suffix}.log")
    }
    
    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter with more detailed information
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
    )
    
    # Create and configure handlers
    handlers = []
    
    # Consolidated log (rotating file handler)
    consolidated_handler = RotatingFileHandler(
        consolidated_log,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    consolidated_handler.setLevel(logging.DEBUG)
    consolidated_handler.setFormatter(formatter)
    handlers.append(consolidated_handler)
    
    # Action-specific handlers based on logger name
    action_handler = None
    name_lower = name.lower()
    
    if 'portfolio' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['portfolio'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'walletsinvested' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['walletsinvested'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'attention' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['attention'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'transaction' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['transaction'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'scheduler' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['scheduler'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'parser' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['parser'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'database' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['database'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'api' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['api'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'smwallettoppnltoken' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['smwallettoppnltoken'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'smwallettoppnltokeninvestment' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['smwallettoppnltokeninvestment'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'volumebot' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['volumebot'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'pumpfun' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['pumpfun'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'dexscreener' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['dexscreener'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    # Add handlers for new analytics framework modules
    elif 'analyticsframework' in name_lower or 'framework/analytics' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['analyticsframework'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'strategy' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['strategy'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    elif 'pushtoken' in name_lower or 'push_token' in name_lower:
        action_handler = RotatingFileHandler(
            action_logs['pushtoken'],
            maxBytes=10*1024*1024,
            backupCount=5
        )
    
    if action_handler:
        action_handler.setLevel(logging.DEBUG)
        action_handler.setFormatter(formatter)
        handlers.append(action_handler)
    
    # Error log handler (for all ERROR level logs)
    error_handler = RotatingFileHandler(
        action_logs['error'],
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    handlers.append(error_handler)
    
    # Console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Add all handlers to logger
    for handler in handlers:
        logger.addHandler(handler)
    
    return logger 