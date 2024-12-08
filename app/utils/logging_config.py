import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler for all logs
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Specific handler for M-PESA logs
    mpesa_handler = RotatingFileHandler(
        'logs/mpesa.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    mpesa_handler.setFormatter(file_formatter)
    mpesa_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Add handlers to root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Configure M-PESA specific logger
    mpesa_logger = logging.getLogger('mpesa')
    mpesa_logger.setLevel(logging.INFO)
    mpesa_logger.addHandler(mpesa_handler)
    
    return logger
