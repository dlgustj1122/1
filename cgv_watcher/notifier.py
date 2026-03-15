from __future__ import annotations

import json
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

    def send_message(self, message: str) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": message,
        }

        try:
            response = requests.post(self.endpoint, data=payload, timeout=self.timeout)
        except requests.RequestException as error:
            LOGGER.warning("Telegram sendMessage network failure: %s", error)
            return False

        if not response.ok:
            LOGGER.error(
                "Telegram sendMessage failed. status=%s body=%s",
                response.status_code,
                response.text,
            )
            return False

        try:
            data = response.json()
        except ValueError:
            return True

        if isinstance(data, dict) and not data.get("ok", True):
            LOGGER.error("Telegram sendMessage rejected: %s", data)
            return False

        return True
