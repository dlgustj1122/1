from __future__ import annotations

import logging

import requests

LOGGER = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 10) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

    @property
    def endpoint(self) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, message: str) -> None:
        payload = {
            "chat_id": self.chat_id,
            "text": message,
        }

        try:
            response = requests.post(self.endpoint, data=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            LOGGER.exception("Telegram sendMessage failed")
            raise
