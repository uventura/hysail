import logging
import os
from datetime import datetime


class BasicLogger:
    """
    Logger utilities using Python's logging library.
    Saves logs to a file with a non-verbose format.
    """

    def __init__(
        self, name: str = "hysail", log_file: str = None, level: int = logging.INFO
    ):
        print(logging.INFO)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        log_file = self._prepare_log_file(log_file)
        self.logger.handlers.clear()
        self._setup_file_handler(log_file, level)

    def _prepare_log_file(self, log_file: str = None) -> str:
        if log_file is None:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            log_file = os.path.join(log_dir, "hysail.log")
        return log_file

    def _setup_file_handler(self, log_file: str, level: int) -> None:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(message)
