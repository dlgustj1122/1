import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from cgv_watcher.models import BookingState, WatchTarget
from cgv_watcher.state_store import StateStore
from cgv_watcher.watcher import CGVBookingWatcher


class TestWatcher(unittest.TestCase):
    def setUp(self) -> None:
        self.target = WatchTarget("프로젝트 헤일메리", "용산아이파크몰", "2026-03-29", "IMAX")

    def test_notify_only_on_first_available(self) -> None:
        parser = Mock()
        parser.fetch.return_value = "<html></html>"
        parser.final_url = "https://redirected.example.com/show"
        parser.last_error = ""
        parser.determine_state.return_value = BookingState.AVAILABLE

        notifier = Mock()
        notifier.send_message.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.json"
            store = StateStore(str(state_path))
            watcher = CGVBookingWatcher(
                parser=parser,
                notifier=notifier,
                state_store=store,
                target=self.target,
                cgv_url="https://example.com",
            )

            watcher.check_once()
            watcher.check_once()

        notifier.send_message.assert_called_once()

    def test_check_once_handles_fetch_error_without_raising(self) -> None:
        parser = Mock()
        parser.fetch.side_effect = RuntimeError("network")
        parser.final_url = "https://example.com"
        parser.last_error = "network"

        notifier = Mock()
        notifier.send_message.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.json"
            store = StateStore(str(state_path))
            watcher = CGVBookingWatcher(
                parser=parser,
                notifier=notifier,
                state_store=store,
                target=self.target,
                cgv_url="https://example.com",
            )

            watcher.check_once()

        notifier.send_message.assert_called_once_with("오류가 발생했습니다.")

    def test_empty_fetch_response_skips_processing_and_notifies_error_once(self) -> None:
        parser = Mock()
        parser.fetch.return_value = ""
        parser.final_url = "https://example.com/blocked"
        parser.last_error = "403"

        notifier = Mock()
        notifier.send_message.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.json"
            store = StateStore(str(state_path))
            watcher = CGVBookingWatcher(
                parser=parser,
                notifier=notifier,
                state_store=store,
                target=self.target,
                cgv_url="https://example.com",
            )

            watcher.check_once()
            watcher.check_once()

            self.assertIsNone(store.load_last_state())

        parser.determine_state.assert_not_called()
        notifier.send_message.assert_called_once_with("오류가 발생했습니다.")


if __name__ == "__main__":
    unittest.main()
