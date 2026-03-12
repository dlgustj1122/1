import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from cgv_watcher.models import BookingState, WatchTarget
from cgv_watcher.state_store import StateStore
from cgv_watcher.watcher import CGVBookingWatcher


class TestWatcher(unittest.TestCase):
    def setUp(self) -> None:
        self.target = WatchTarget("영화", "강남", "2026-03-20", "IMAX")

    def test_notify_only_on_first_available(self) -> None:
        parser = Mock()
        parser.fetch.return_value = "<html></html>"
        parser.determine_state.return_value = BookingState.AVAILABLE

        notifier = Mock()

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
