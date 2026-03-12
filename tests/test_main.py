import importlib
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

            class BeautifulSoup:  # pragma: no cover - import stub
                def __init__(self, *_args, **_kwargs):
                    pass

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


if __name__ == "__main__":
    unittest.main()
