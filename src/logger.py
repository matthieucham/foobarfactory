import logging

from logging.config import fileConfig

fileConfig('logging.ini')

logging.getLogger().debug("Logger configured")
