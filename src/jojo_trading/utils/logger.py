import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Setup Logs Directory
# logger.py lives at src/jojo_trading/utils/logger.py; parents[3] is the
# project root. Keeping logs inside the project avoids permission issues when
# tests are launched from different workspace folders.
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str = "jojo_trading", log_file: str = "app.log", level=logging.INFO):
    """
    Setup a logger with RotatingFileHandler and StreamHandler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if logger is already setup
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. Rotating File Handler (Max 10MB, keep 5 backups)
    file_path = os.path.join(LOG_DIR, log_file)
    file_handler = RotatingFileHandler(
        file_path, 
        maxBytes=10*1024*1024, # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # 2. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create Global Logger
logger = setup_logger()
