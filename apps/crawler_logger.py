import logging, inspect, os

INFO_LOG_PATH = "logs\info.txt"
ERROR_LOG_PATH = "logs\error.txt"


class CrawlerLogger:
    def __init__(self, info_logfile=INFO_LOG_PATH, error_logfile=ERROR_LOG_PATH):
        # self._initialize_log_files(INFO_LOG_PATH, ERROR_LOG_PATH)
        self.info_logger = self.setup_logger("info_logger", info_logfile, logging.INFO)
        self.error_logger = self.setup_logger(
            "error_logger", error_logfile, logging.ERROR
        )

    def _initialize_log_files(self, info_log_path, error_log_path):
        for log_path in [info_log_path, error_log_path]:
            if os.path.exists(log_path):
                os.remove(log_path)

    def setup_logger(self, logger_name, log_file, log_level):
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        if logger.hasHandlers():
            logger.handlers.clear()

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        return logger

    def info(self, message):
        self.info_logger.info(message)

    def error(self, message):
        caller_class = inspect.stack()[1][0].f_locals.get("self", None)
        if caller_class:
            class_name = caller_class.__class__.__name__
            error_method = inspect.stack()[1][3]
            message = f"{class_name}: {error_method} - {message}"
        self.error_logger.error(message)

    def close(self):
        for handler in self.info_logger.handlers:
            handler.close()
        for handler in self.error_logger.handlers:
            handler.close()
