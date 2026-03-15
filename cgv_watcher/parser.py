from __future__ import annotations

import logging
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

from .models import BookingState, WatchTarget

LOGGER = logging.getLogger(__name__)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.cgv.co.kr/",
}


@dataclass
class CGVParser:
    session: requests.Session | None = None
    final_url: str = ""
    last_error: str = ""
    _default_headers: dict[str, str] = field(default_factory=lambda: DEFAULT_HEADERS.copy())

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = requests.Session()
        self.session.headers.update(self._default_headers)

    def fetch(self, url: str, timeout: int = 10) -> str:
        assert self.session is not None
        self.final_url = url
        self.last_error = ""

        try:
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            self.final_url = response.url or url
            response.raise_for_status()
            return response.text
        except requests.RequestException as error:
            self.last_error = str(error)
            LOGGER.warning("Network error while fetching CGV page: %s (%s)", url, error)
            return ""
        except Exception as error:  # noqa: BLE001
            self.last_error = str(error)
            LOGGER.warning("Unexpected error while fetching CGV page: %s (%s)", url, error)
            return ""

    def determine_state(self, html: str, target: WatchTarget) -> BookingState:
        soup = BeautifulSoup(html, "html.parser")
        scope_text = self._extract_scope_text(soup, target)
        normalized = " ".join(scope_text.split()).lower()

        if not normalized:
            LOGGER.warning("HTML structure may have changed: extracted text is empty")
            return BookingState.UNKNOWN

        preparing_tokens = ["예매준비중", "coming soon", "준비중", "오픈예정"]
        unavailable_tokens = ["예매불가", "매진", "종영", "unavailable", "sold out"]
        available_tokens = ["예매하기", "booking", "buy ticket", "book now", "seat"]

        if self._contains_any(normalized, preparing_tokens):
            return BookingState.PREPARING
        if self._contains_any(normalized, unavailable_tokens):
            return BookingState.UNAVAILABLE
        if self._contains_any(normalized, available_tokens):
            return BookingState.AVAILABLE

        LOGGER.warning(
            "HTML structure may have changed: state not inferred. snippet=%s", normalized[:300]
        )
        return BookingState.UNKNOWN

    @staticmethod
    def _contains_any(text: str, tokens: list[str]) -> bool:
        lowered_tokens = [token.lower() for token in tokens]
        return any(token in text for token in lowered_tokens)

    @staticmethod
    def _extract_scope_text(soup: BeautifulSoup, target: WatchTarget) -> str:
        target_tokens = [
            target.movie_name.lower(),
            target.theater_name.lower(),
            target.date.lower(),
            target.movie_format.lower(),
        ]

        candidate_strings: list[str] = []
        for element in soup.find_all(string=True):
            stripped = element.strip()
            if not stripped:
                continue
            lowered = stripped.lower()
            if any(token in lowered for token in target_tokens if token):
                parent = element.parent
                if parent:
                    candidate_strings.append(parent.get_text(" ", strip=True))

        if candidate_strings:
            return " ".join(candidate_strings)

        return soup.get_text(" ", strip=True)
