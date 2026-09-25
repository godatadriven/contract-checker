"""Unit tests for the console logger setup."""

from __future__ import annotations

import logging

from contract_checker.logger import setup_console_logger


class TestSetupConsoleLogger:
    """Test root-logger configuration for CLI use."""

    def teardown_method(self) -> None:
        """Leave the root logger clean for other tests."""
        logging.getLogger("").handlers.clear()

    def test_repeated_setup_does_not_accumulate_handlers(self) -> None:
        """Calling setup twice must not duplicate every log message."""
        setup_console_logger(False)
        setup_console_logger(False)
        assert len(logging.getLogger("").handlers) == 1

    def test_default_level_is_warning(self) -> None:
        """Without verbosity, INFO/DEBUG messages are hidden; warnings show."""
        setup_console_logger(False)
        handler = logging.getLogger("").handlers[0]
        assert handler.level == logging.WARNING

    def test_verbose_level_is_debug(self) -> None:
        """With verbosity, everything down to DEBUG is shown."""
        setup_console_logger(True)
        handler = logging.getLogger("").handlers[0]
        assert handler.level == logging.DEBUG

    def test_default_format_is_plain(self) -> None:
        """Non-verbose messages read as tool output, not timestamped log lines."""
        setup_console_logger(False)
        handler = logging.getLogger("").handlers[0]
        record = logging.LogRecord("root", logging.ERROR, "", 0, "boom", None, None)
        assert handler.format(record) == "ERROR: boom"

    def test_verbose_format_has_timestamp(self) -> None:
        """Verbose messages carry timestamp and level for troubleshooting."""
        setup_console_logger(True)
        handler = logging.getLogger("").handlers[0]
        record = logging.LogRecord("root", logging.DEBUG, "", 0, "boom", None, None)
        formatted = handler.format(record)
        assert "DEBUG" in formatted
        assert "boom" in formatted
        assert " - " in formatted  # timestamped multi-part format
