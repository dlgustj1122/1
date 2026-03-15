from __future__ import annotations

import logging

from .models import BookingState, WatchTarget
from .notifier import TelegramNotifier
from .parser import CGVParser
from .state_store import StateStore

LOGGER = logging.getLogger(__name__)


class CGVBookingWatcher:
    def __init__(
        self,
        parser: CGVParser,
        notifier: TelegramNotifier,
        state_store: StateStore,
        target: WatchTarget,
        cgv_url: str,
    ) -> None:
        self.parser = parser
        self.notifier = notifier
        self.state_store = state_store
        self.target = target
        self.cgv_url = cgv_url

    def check_once(self) -> None:
        try:
            html = self.parser.fetch(self.cgv_url)
            if not html.strip():
                LOGGER.warning("Skipping check: empty response from CGV")
                return
            current_state = self.parser.determine_state(html, self.target)
        except Exception as error:  # noqa: BLE001
            LOGGER.warning("Watcher check failed while fetching/parsing: %s", error)
            return

        last_state = self.state_store.load_last_state()

        LOGGER.info(
            "Current state=%s last_state=%s target=%s",
            current_state.value,
            last_state.value if last_state else None,
            self.target.to_dict(),
        )

        if self._should_notify_available(last_state, current_state):
            message = self._build_available_message()
            sent = self.notifier.send_message(message)
            if not sent:
                LOGGER.warning("Availability detected but Telegram notification failed")

        if last_state != current_state:
            try:
                self.state_store.save_last_state(current_state)
            except Exception as error:  # noqa: BLE001
                LOGGER.warning("Failed to persist watcher state: %s", error)

    def _should_notify_available(
        self,
        last_state: BookingState | None,
        current_state: BookingState,
    ) -> bool:
        return current_state == BookingState.AVAILABLE and last_state != BookingState.AVAILABLE

    def _build_available_message(self) -> str:
        format_text = self.target.movie_format or "일반"
        return (
            "[CGV 예매 오픈 감지]\n"
            f"영화: {self.target.movie_name}\n"
            f"극장: {self.target.theater_name}\n"
            f"날짜: {self.target.date}\n"
            f"포맷: {format_text}\n"
            f"URL: {self.cgv_url}"
        )
