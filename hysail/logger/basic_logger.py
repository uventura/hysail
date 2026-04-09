import logging
import os
from datetime import datetime


class BasicLogger:
    """
    Logger utilities using Python's logging library.
    Saves logs to a file with a non-verbose format.
    """

    def __init__(
        self,
        name: str = "hysail",
        log_file: str = None,
        level: list = [logging.INFO, logging.DEBUG],
    ):
        console_handler_level, file_handler_level = level

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        log_file = self._prepare_log_file(log_file)
        self.logger.handlers.clear()

        self._setup_console_handler(console_handler_level)
        self._setup_file_handler(log_file, file_handler_level)

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
        file_handler.setFormatter(self._formatter())

        self.logger.addHandler(file_handler)

    def _setup_console_handler(self, level: int) -> None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(self._formatter())

        self.logger.addHandler(console_handler)

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

    def clear_logs(self) -> None:
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                os.remove(handler.baseFilename)

    def _formatter(self):
        return logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
