from __future__ import annotations

import logging
import time
from typing import Callable

LOGGER = logging.getLogger(__name__)


class PollScheduler:
    def __init__(self, interval_seconds: int) -> None:
        self.interval_seconds = interval_seconds

    def run_forever(self, job: Callable[[], None]) -> None:
        LOGGER.info("Starting scheduler: every %s seconds", self.interval_seconds)
        while True:
            started = time.time()
            job()
            elapsed = time.time() - started
            sleep_for = max(self.interval_seconds - elapsed, 0)
            time.sleep(sleep_for)
