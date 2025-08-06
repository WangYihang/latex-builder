"""Structured logging configuration and utilities."""

import logging
import sys
from typing import Optional

import structlog


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Setup structured logging configuration.

    Args:
        verbose: Enable debug logging
        quiet: Suppress all output except errors
    """
    # Determine log level
    if quiet:
        min_level = logging.ERROR
    elif verbose:
        min_level = logging.DEBUG
    else:
        min_level = logging.INFO

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(min_level=min_level),
        logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name, defaults to calling module

    Returns:
        Configured structlog logger instance
    """
    logger_name = name or "latex-builder"
    return structlog.get_logger(logger_name)
