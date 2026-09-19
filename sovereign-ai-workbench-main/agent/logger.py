import json
import logging
from pathlib import Path
from datetime import datetime


LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("sovereign_ai_agent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(
        LOG_DIR / "agent_audit.log",
        encoding="utf-8",
    )

    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(message)s")
    )

    logger.addHandler(file_handler)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def make_event(event_type: str, **details) -> dict:
    return {
        "timestamp": now_iso(),
        "event": event_type,
        **details,
    }


def write_local_audit(event: dict) -> None:
    logger.info(json.dumps(event, ensure_ascii=False, default=str))