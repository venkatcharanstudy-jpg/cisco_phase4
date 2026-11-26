import logging
import os
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

SENSITIVE_KEYS = {"password", "token", "api_key", "authorization", "secret"}
REDACTED = "***"
DEFAULT_LOG_FILE = "netpulse.log"


def redact_sensitive(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    for key in list(event_dict):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = REDACTED
    return event_dict


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            redact_sensitive,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    # Only the "netpulse" namespace is handled here; uvicorn and root loggers are untouched.
    logger = logging.getLogger("netpulse")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    formatter = logging.Formatter("%(message)s")
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    logger.addHandler(console)
    log_file = os.getenv("NETPULSE_LOG_FILE", DEFAULT_LOG_FILE)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
