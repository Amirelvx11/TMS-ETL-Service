import logging
import os
import sys

_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

def get_logger(name: str = "tms_etl") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = _LEVELS.get(os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(format)

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
