import json
import time
from pathlib import Path
from typing import Any, Dict


class TelemetryLogger:
    def __init__(self, path: str = "telemetry.log"):
        self.path = Path(path)
        # Append mode; create file if needed.
        self._fh = self.path.open("a", encoding="utf-8")

    def log(self, event_type: str, payload: Dict[str, Any]):
        record = {
            "ts": time.time(),
            "type": event_type,
            "data": payload,
        }
        self._fh.write(json.dumps(record) + "\n")
        self._fh.flush()

    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None
