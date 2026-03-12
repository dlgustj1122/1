from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from .models import BookingState, WatchTarget
from .notifier import TelegramNotifier
from .parser import CGVParser
from .state_store import StateStore

LOGGER = logging.getLogger(__name__)


@dataclass
class CGVBookingWatcher:
    parser: CGVParser
    notifier: TelegramNotifier
    state_store: StateStore
    target: WatchTarget
    cgv_url: str

    def check_once(self) -> BookingState:
        try:
            html = self.parser.fetch(self.cgv_url)
        except requests.RequestException:
            LOGGER.exception("Network error while fetching CGV page")
            return BookingState.UNKNOWN

        try:
            current_state = self.parser.determine_state(html, self.target)
        except Exception:  # noqa: BLE001
            LOGGER.exception("HTML structure may have changed; parser failed")
            return BookingState.UNKNOWN

        self._handle_state_change(current_state)
        return current_state

    def _handle_state_change(self, current_state: BookingState) -> None:
        last_state = self.state_store.load_last_state()

        if current_state == BookingState.AVAILABLE and last_state != BookingState.AVAILABLE:
            self._notify_available()

        if current_state != last_state:
            self.state_store.save_last_state(current_state)
            LOGGER.info("State updated: %s -> %s", last_state, current_state)
        else:
            LOGGER.info("State unchanged: %s", current_state)

    def _notify_available(self) -> None:
        message = (
            "✅ CGV 예매 가능 감지!\n"
            f"영화: {self.target.movie_name}\n"
            f"극장: {self.target.theater_name}\n"
            f"날짜: {self.target.date}\n"
            f"포맷: {self.target.movie_format}\n"
            f"링크: {self.cgv_url}"
        )
        try:
            self.notifier.send_message(message)
            LOGGER.info("Telegram notification sent")
        except requests.RequestException:
            LOGGER.exception("Telegram notification failed")
