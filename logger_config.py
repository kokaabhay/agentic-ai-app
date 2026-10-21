import logging
from logging.handlers import RotatingFileHandler
from config import LOGS_DIR, LOG_LEVEL

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_configured = False

def setup_logging() -> None:
    global _configured
    if _configured:
        return
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT)
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    if not any(getattr(h, "_agentic_handler", False) for h in root.handlers):
        for handler in [
            RotatingFileHandler(LOGS_DIR / "app.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"),
            logging.StreamHandler(),
        ]:
            handler.setFormatter(formatter)
            handler._agentic_handler = True
            root.addHandler(handler)
    for name, filename in [
        ("agent_activity", "agent_activity.log"),
        ("communication", "communication.log"),
        ("tool_activity", "tool_activity.log"),
    ]:
        log = logging.getLogger(name)
        log.setLevel(level)
        log.propagate = False
        if not log.handlers:
            handler = RotatingFileHandler(LOGS_DIR / filename, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
            handler.setFormatter(formatter)
            log.addHandler(handler)
    _configured = True
