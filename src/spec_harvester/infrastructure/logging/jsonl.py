from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

EVENT_RUN_STARTED = "run_started"
EVENT_FETCH_SUCCESS = "fetch_success"
EVENT_FETCH_ERROR = "fetch_error"
EVENT_SAVED = "saved"
EVENT_DEDUP_HIT = "dedup_hit"
EVENT_RUN_FINISHED = "run_finished"


class JsonlEventLogger:
    def __init__(self, path: Path, *, base_fields: dict[str, object] | None = None) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._base_fields = base_fields or {}

    def emit(self, event: str, **fields: object) -> None:
        row = {
            "event": event,
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            **self._base_fields,
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
