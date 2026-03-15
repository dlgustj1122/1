import importlib
import os
import unittest
from unittest.mock import Mock, patch

main = importlib.import_module("main")


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
    def test_poll_interval_falls_back_to_default_on_invalid_value(self) -> None:
        self.assertEqual(main._poll_interval_or_default("abc", 60), 60)
        self.assertEqual(main._poll_interval_or_default("0", 60), 60)
        self.assertEqual(main._poll_interval_or_default("-5", 60), 60)
        self.assertEqual(main._poll_interval_or_default("120", 60), 120)

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
