import sys
from src.modules.core import Logger

logger = Logger("test_logger")
print("STDOUT_CHECK")
logger.info("LOG_CHECK")
