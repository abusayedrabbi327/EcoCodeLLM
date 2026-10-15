"""
logger.py — Structured logging for the EcoCode-LLM framework.

Provides a pre-configured logger that outputs to both console (with Rich
formatting) and a rotating log file. All framework modules import and
use this logger for consistent output.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

from rich.logging import RichHandler
from rich.console import Console


# Shared Rich console instance
console = Console(legacy_windows=False)

# Log file location
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "outputs" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str = "ecocode", level: int = logging.INFO) -> logging.Logger:
    """
    Create or retrieve a named logger with Rich console + file handlers.

    Args:
        name: Logger name (typically the module name).
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # ---- Console handler (Rich formatted) ----
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )
    rich_handler.setLevel(level)
    rich_format = logging.Formatter("%(message)s")
    rich_handler.setFormatter(rich_format)
    logger.addHandler(rich_handler)

    # ---- File handler (plain text) ----
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = _LOG_DIR / f"ecocode_{timestamp}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # File captures everything
    file_format = logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger
