"""
Central logging configuration for Skipper project
All logs are placed in the logs/ directory
"""

import logging
from pathlib import Path
from datetime import datetime

# Central log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def get_logger(name, log_to_file=True, level=logging.INFO):
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (typically __name__ from calling module)
        log_to_file: Whether to also log to file (default: True)
        level: Logging level (default: INFO)
    
    Returns:
        logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        # Extract module name for log file
        module_name = name.split('.')[-1] if '.' in name else name
        log_file = LOG_DIR / f"{module_name}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_log_file_path(name, extension='log', timestamp=True):
    """
    Get a path for a log file in the logs directory
    
    Args:
        name: Base name for the log file
        extension: File extension (default: 'log')
        timestamp: Whether to include timestamp in filename (default: True)
    
    Returns:
        Path object for the log file
    """
    if timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{ts}.{extension}"
    else:
        filename = f"{name}.{extension}"
    
    return LOG_DIR / filename

def setup_basic_logging(level=logging.INFO):
    """
    Setup basic logging configuration for the entire project
    This should be called once at application startup
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Root logger configuration
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / 'skipper.log')
        ]
    )

# Convenience function for getting timestamped data files
def get_data_log_path(name, extension='csv'):
    """
    Get a path for a data log file (CSV, JSON, etc.) with timestamp
    
    Args:
        name: Base name for the data file
        extension: File extension (default: 'csv')
    
    Returns:
        Path object for the data file
    """
    return get_log_file_path(name, extension=extension, timestamp=True)
