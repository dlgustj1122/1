import unittest
from unittest.mock import Mock, patch

import requests

from cgv_watcher.notifier import TelegramNotifier


class TestTelegramNotifier(unittest.TestCase):
    @patch("cgv_watcher.notifier.requests.post")
    def test_send_message_returns_false_on_http_400(self, mock_post: Mock) -> None:
        response = Mock()
        response.ok = False
        response.status_code = 400
        response.text = "Bad Request: chat not found"
        mock_post.return_value = response

        notifier = TelegramNotifier("token", "invalid-chat")
        self.assertFalse(notifier.send_message("hello"))

    @patch("cgv_watcher.notifier.requests.post")
    def test_send_message_returns_false_on_network_error(self, mock_post: Mock) -> None:
        mock_post.side_effect = requests.RequestException("network")

        notifier = TelegramNotifier("token", "123")
        self.assertFalse(notifier.send_message("hello"))

    @patch("cgv_watcher.notifier.requests.post")
    def test_send_message_returns_true_on_success(self, mock_post: Mock) -> None:
        response = Mock()
        response.ok = True
        response.json.return_value = {"ok": True}
        mock_post.return_value = response

        notifier = TelegramNotifier("token", "123")
        self.assertTrue(notifier.send_message("hello"))


if __name__ == "__main__":
    unittest.main()
