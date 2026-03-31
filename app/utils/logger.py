"""
Logging configuration for the application.

Sets up structured logging (using loguru when available, fallback to stdlib).
"""

import sys
import logging
from pathlib import Path

try:
    from loguru import logger as _logger
    
    # Remove default handler
    _logger.remove()
    
    # Add console handler with color
    _logger.add(
        sys.stdout,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )
    
    # Add file handler for all logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    _logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="500 MB",
        retention="10 days",
    )
    
    # Add file handler for errors only
    _logger.add(
        log_dir / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="500 MB",
        retention="10 days",
    )
    
    logger = _logger

except ImportError:
    # Fallback to standard logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    )
    logger = logging.getLogger(__name__)
