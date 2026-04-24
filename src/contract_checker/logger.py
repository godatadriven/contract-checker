import logging
import os


def setup_console_logger(verbosity: bool) -> None:
    """Initialise a logger with the specified log level."""
    logger = logging.getLogger("")
    logger.propagate = True
    logger.setLevel(logging.DEBUG)

    if os.getenv("LOG_LEVEL") == "DEBUG" or verbosity:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
