import logging
import os


def setup_console_logger(verbosity: bool) -> None:
    """Initialise the root logger for CLI use.

    By default only warnings and errors are shown, in a plain
    ``LEVEL: message`` format so they read as tool output rather than log
    lines. With ``verbosity`` (or ``LOG_LEVEL=DEBUG``) everything down to
    DEBUG is shown with timestamps for troubleshooting.

    Existing handlers are replaced, so repeated calls (tests, programmatic
    use) do not accumulate handlers and duplicate every message.
    """
    logger = logging.getLogger("")
    logger.propagate = True
    logger.setLevel(logging.DEBUG)

    if os.getenv("LOG_LEVEL") == "DEBUG" or verbosity:
        log_level = logging.DEBUG
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    else:
        log_level = logging.WARNING
        formatter = logging.Formatter("%(levelname)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    # Replace, don't append: repeated setup must not duplicate output.
    logger.handlers.clear()
    logger.addHandler(console_handler)
