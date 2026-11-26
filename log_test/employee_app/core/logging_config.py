import logging
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "employee_app.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
APP_LOGGER_NAME = "employee_app"


def setup_logging(level: int = logging.INFO) -> None:
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    if app_logger.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    app_logger.setLevel(level)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(stream_handler)
    app_logger.propagate = False
