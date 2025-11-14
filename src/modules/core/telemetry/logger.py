import logging
from typing import Optional


class Logger:
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str, **kwargs):
        self.logger.info(message, **kwargs)

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        self.logger.error(message, exc_info=exc_info, **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **kwargs)

    def exception(self, message: str, **kwargs):
        self.logger.exception(message, **kwargs)


def get_logger(name: str, level: int = logging.INFO) -> Logger:
    """
    Factory function to create a Logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)

    Returns:
        Logger instance
    """
    return Logger(name, level)
