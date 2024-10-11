"""
Abstraction layer over standard logging library to provide the option for
detaching from the standard logger
"""

import logging


DEBUG = logging.DEBUG
INFO = logging.DEBUG
WARNING = logging.DEBUG
ERROR = logging.DEBUG


def set_level(level):
    logging.getLogger().setLevel(level)


def info(*args, **kwargs):
    logging.info(*args, **kwargs)


def warning(*args, **kwargs):
    logging.warning(*args, **kwargs)


def debug(*args, **kwargs):
    logging.debug(*args, **kwargs)


def error(*args, **kwargs):
    logging.error(*args, **kwargs)


def critical(*args, **kwargs):
    logging.critical(*args, **kwargs)


