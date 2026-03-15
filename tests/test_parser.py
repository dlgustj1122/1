import unittest

from cgv_watcher.models import BookingState, WatchTarget
from cgv_watcher.parser import CGVParser


class TestCGVParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = CGVParser()
        self.target = WatchTarget(
            movie_name="프로젝트 헤일메리",
            theater_name="용산아이파크몰",
            date="2026-03-29",
            movie_format="IMAX",
        )

    def test_determine_state_available(self) -> None:
        html = """
        <html><body>
            <div>프로젝트 헤일메리 용산아이파크몰 2026-03-29 IMAX 예매하기</div>
        </body></html>
        """
        self.assertEqual(self.parser.determine_state(html, self.target), BookingState.AVAILABLE)

    def test_determine_state_preparing(self) -> None:
        html = """
        <html><body>
            <div>프로젝트 헤일메리 용산아이파크몰 2026-03-29 IMAX 예매준비중</div>
        </body></html>
        """
        self.assertEqual(self.parser.determine_state(html, self.target), BookingState.PREPARING)
