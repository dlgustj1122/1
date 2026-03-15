import unittest
from unittest.mock import patch

from cgv_watcher.scheduler import PollScheduler


class TestPollScheduler(unittest.TestCase):
    @patch("cgv_watcher.scheduler.time.sleep", side_effect=KeyboardInterrupt)
    def test_scheduler_continues_after_job_error(self, _mock_sleep) -> None:
        scheduler = PollScheduler(interval_seconds=1)
        calls = {"count": 0}

        def job() -> None:
            calls["count"] += 1
            raise RuntimeError("boom")

        with self.assertRaises(KeyboardInterrupt):
            scheduler.run_forever(job)

        self.assertEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
