import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


def configure_logging(level: int = logging.INFO) -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def log_event(event: str, **fields: Any) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    logging.getLogger("coproduct").info(json.dumps(payload, ensure_ascii=False))

