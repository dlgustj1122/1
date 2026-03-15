import unittest
from unittest.mock import Mock

import requests

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

    def test_fetch_returns_empty_string_on_network_error(self) -> None:
        session = Mock()
        session.get.side_effect = requests.RequestException("403")
        parser = CGVParser(session=session)

        result = parser.fetch("https://www.cgv.co.kr/ticket/")

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
