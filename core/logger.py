"""
Centralized Application Logger for AI-Powered Campus Helpdesk Assistant.
Provides rotating file logs to logs/app.log with automatic secret redaction
(API keys, sensitive tokens) and clean console output.
"""

import os
import re
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import settings

LOGS_DIR = settings.BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"

# Regex pattern for Google AI API keys or general API tokens
SECRET_PATTERN = re.compile(r'(?:AIza[0-9A-Za-z-_]{35}|[0-9a-zA-Z]{32,45})')


class SecretRedactingFormatter(logging.Formatter):
    """Logging formatter that scrubs API keys and sensitive tokens from log messages."""
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        # Redact any matches that look like API keys
        return SECRET_PATTERN.sub("[REDACTED_API_KEY]", original)


def get_logger(name: str = "campus_helpdesk") -> logging.Logger:
    """
    Returns a configured rotating logger for the application.
    Writes formatted, redacted logs to logs/app.log.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Ensure logs directory exists
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Create rotating file handler (max 2MB per file, 3 backups)
    try:
        file_handler = RotatingFileHandler(
            str(LOG_FILE),
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        formatter = SecretRedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s:%(module)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        # Fallback to null handler if filesystem prevents file creation
        logger.addHandler(logging.NullHandler())

    return logger


# Global application logger instance
logger = get_logger("campus_helpdesk")
