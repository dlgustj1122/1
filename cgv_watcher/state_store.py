from __future__ import annotations

import json
import logging
from pathlib import Path

from .models import BookingState

LOGGER = logging.getLogger(__name__)


class StateStore:
    def __init__(self, path: str = "watcher_state.json") -> None:
        self.path = Path(path)

    def load_last_state(self) -> BookingState | None:
        if not self.path.exists():
            return None

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            value = data.get("last_state")
            if value is None:
                return None
            return BookingState(value)
        except (json.JSONDecodeError, ValueError):
            LOGGER.exception("Failed to load state file: %s", self.path)
            return None

    def save_last_state(self, state: BookingState) -> None:
        payload = {"last_state": state.value}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
