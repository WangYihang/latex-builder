"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys

import structlog


def setup(*, verbose: bool = False, quiet: bool = False) -> None:
    """Configure structlog for the application."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(min_level=level),
        logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get(name: str | None = None) -> structlog.BoundLogger:
    """Get a named logger."""
    return structlog.get_logger(name or "latex-builder")
