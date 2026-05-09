import logging
import sys

SPACE = " " * 4
LOG_FORMAT = "%(levelname)s:" + SPACE +" %(message)s | [%(name)s] | %(funcName)s | %(asctime)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger().setLevel(level)
