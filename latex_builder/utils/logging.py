"""Logging configuration and utilities."""

import logging
from typing import Optional

try:
    from rich.logging import RichHandler
except ImportError:
    RichHandler = None

# Global logger cache
_loggers = {}


def setup_logging(verbose: bool = False) -> None:
    """
    Setup global logging configuration.
    
    Args:
        verbose: Enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    handlers = []
    if RichHandler:
        handlers.append(RichHandler(rich_tracebacks=True))
    else:
        handlers.append(logging.StreamHandler())
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
        force=True
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with rich formatting.
    
    Args:
        name: Logger name, defaults to calling module
        
    Returns:
        Configured logger instance
    """
    if name is None:
        name = "latex-builder"
    
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger
    
    return _loggers[name]
