import logging

logger = logging.getLogger(__name__)

# the handler determines where the logs go: stdout/file
handler = logging.StreamHandler()


logger.addHandler(handler)
logger.setLevel(logging.WARNING)
