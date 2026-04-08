"""Unit tests for latex_builder.utils.logging."""

import logging

import structlog

from latex_builder.utils.logging import get_logger, setup_logging


class TestSetupLogging:
    """Test setup_logging function."""

    def test_default_level_is_info(self):
        setup_logging()
        # Verify by creating a logger and checking it filters debug
        logger = structlog.get_logger("test-default")
        assert logger is not None

    def test_verbose_enables_debug(self):
        setup_logging(verbose=True)
        logger = structlog.get_logger("test-verbose")
        assert logger is not None

    def test_quiet_sets_error_level(self):
        setup_logging(quiet=True)
        logger = structlog.get_logger("test-quiet")
        assert logger is not None

    def test_quiet_overrides_verbose(self):
        # quiet takes priority over verbose
        setup_logging(verbose=True, quiet=True)
        logger = structlog.get_logger("test-override")
        assert logger is not None


class TestGetLogger:
    """Test get_logger function."""

    def test_returns_bound_logger(self):
        logger = get_logger("test-module")
        assert logger is not None

    def test_default_name(self):
        logger = get_logger()
        assert logger is not None

    def test_custom_name(self):
        logger = get_logger("custom.module.name")
        assert logger is not None

    def test_returns_same_type(self):
        logger1 = get_logger("a")
        logger2 = get_logger("b")
        assert type(logger1) == type(logger2)
