import importlib
import os
import re
import sys
import types
import unittest
from unittest.mock import Mock, patch


def _import_main_with_fallback_stubs():
    try:
        return importlib.import_module("main")
    except ModuleNotFoundError:
        if "dotenv" not in sys.modules:
            dotenv = types.ModuleType("dotenv")
            dotenv.load_dotenv = lambda: None
            sys.modules["dotenv"] = dotenv

        if "requests" not in sys.modules:
            requests = types.ModuleType("requests")

            class RequestException(Exception):
                pass

            class Session:
                def get(self, *_args, **_kwargs):
                    raise NotImplementedError

            requests.RequestException = RequestException
            requests.Session = Session
            requests.post = lambda *_args, **_kwargs: None
            sys.modules["requests"] = requests

        if "bs4" not in sys.modules:
            bs4 = types.ModuleType("bs4")

            class _Parent:
                def __init__(self, text: str) -> None:
                    self._text = text

                def get_text(self, _separator: str = " ", strip: bool = False) -> str:
                    return self._text.strip() if strip else self._text

            class _TextNode(str):
                def __new__(cls, value: str, parent: _Parent):
                    obj = str.__new__(cls, value)
                    obj.parent = parent
                    return obj

            class BeautifulSoup:  # pragma: no cover - import stub
                def __init__(self, html: str, *_args, **_kwargs):
                    self._html = html

                def find_all(self, string: bool = False):
                    if not string:
                        return []
                    chunks = re.findall(r">([^<>]+)<", self._html)
                    nodes = []
                    for chunk in chunks:
                        text = chunk.strip()
                        if text:
                            parent = _Parent(text)
                            nodes.append(_TextNode(text, parent))
                    return nodes

                def get_text(self, _separator: str = " ", strip: bool = False) -> str:
                    text = re.sub(r"<[^>]+>", " ", self._html)
                    text = " ".join(text.split())
                    return text.strip() if strip else text

            bs4.BeautifulSoup = BeautifulSoup
            sys.modules["bs4"] = bs4

        return importlib.import_module("main")


main = _import_main_with_fallback_stubs()


class TestMainLifecycleNotifications(unittest.TestCase):
    @patch("main.setup_logging")
    @patch("main.PollScheduler")
    @patch("main.build_watcher")
    def test_main_sends_start_and_shutdown_messages_on_keyboard_interrupt(
        self,
        mock_build_watcher,
        mock_scheduler_cls,
        _mock_setup_logging,
    ) -> None:
        notifier = Mock()
        watcher = Mock()
        watcher.notifier = notifier

        mock_build_watcher.return_value = (watcher, 10)

        scheduler = Mock()
        scheduler.run_forever.side_effect = KeyboardInterrupt
        mock_scheduler_cls.return_value = scheduler

        main.main()

        notifier.send_message.assert_any_call("시작됐습니다.")
        notifier.send_message.assert_any_call("종료됐습니다.")
        self.assertEqual(notifier.send_message.call_count, 2)
        scheduler.run_forever.assert_called_once_with(watcher.check_once)


class TestEnvLoading(unittest.TestCase):
    @patch("main.load_dotenv")
    def test_load_env_accepts_alias_and_defaults(self, _mock_load_dotenv: Mock) -> None:
        with patch.dict(
            os.environ,
            {
                "영화제목": "프로젝트 헤일메리",
                "CGV_THEATER_NAME": "용산아이파크몰",
                "CGV_DATE": "2026-03-29",
                "BOT_TOKEN": "abc123\\n",
                "CHAT_ID": "dvd1245",
            },
            clear=True,
        ):
            env = main.load_env_or_raise()

        self.assertEqual(env["CGV_MOVIE_NAME"], "프로젝트 헤일메리")
        self.assertEqual(env["CGV_URL"], main.DEFAULT_CGV_URL)
        self.assertEqual(env["CGV_FORMAT"], "")
        self.assertEqual(env["TELEGRAM_BOT_TOKEN"], "abc123")

    @patch("main.load_dotenv")
    def test_load_env_raises_for_missing_required_keys(self, _mock_load_dotenv: Mock) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                main.load_env_or_raise()

        self.assertIn("Missing required env vars", str(context.exception))


if __name__ == "__main__":
    unittest.main()
