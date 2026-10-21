
import logging
from logging.handlers import RotatingFileHandler

from config import LOGS_DIR, LOG_LEVEL

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | "
    "%(name)s | %(message)s"
)

_configured = False


def setup_logging() -> None:
    global _configured

    if _configured:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)
    level = getattr(logging, LOG_LEVEL, logging.INFO)

    # General application log.
    app_handler = RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setFormatter(formatter)

    # Console output is useful while developing.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(console_handler)

    # Dedicated activity logs.
    for logger_name, filename in [
        ("agent_activity", "agent_activity.log"),
        ("communication", "communication.log"),
        ("tool_activity", "tool_activity.log"),
    ]:
        activity_logger = logging.getLogger(logger_name)
        activity_logger.setLevel(level)
        activity_logger.propagate = False

        handler = RotatingFileHandler(
            LOGS_DIR / filename,
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        activity_logger.addHandler(handler)

    _configured = True
