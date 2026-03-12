from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from .models import BookingState, WatchTarget

LOGGER = logging.getLogger(__name__)


@dataclass
class CGVParser:
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = requests.Session()

    def fetch(self, url: str, timeout: int = 10) -> str:
        assert self.session is not None
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text

    def determine_state(self, html: str, target: WatchTarget) -> BookingState:
        """Infer booking state from CGV page html using keyword heuristics."""
        soup = BeautifulSoup(html, "html.parser")

        scope_text = self._extract_scope_text(soup, target)
        normalized = " ".join(scope_text.split()).lower()

        if not normalized:
            LOGGER.warning("HTML parsing produced empty text scope for target: %s", target)
            return BookingState.UNKNOWN

        # 우선순위: 준비중/불가를 먼저 판별해 "예매" 일반 토큰 오탐을 피한다.
        available_tokens = ["예매하기", "booking", "buy ticket", "book now", "seat"]
        preparing_tokens = ["예매준비중", "coming soon", "준비중", "open 예정"]
        unavailable_tokens = ["예매불가", "매진", "종영", "unavailable", "sold out"]

        if self._contains_any(normalized, preparing_tokens):
            return BookingState.PREPARING
        if self._contains_any(normalized, unavailable_tokens):
            return BookingState.UNAVAILABLE
        if self._contains_any(normalized, available_tokens):
            return BookingState.AVAILABLE

        LOGGER.warning(
            "Could not confidently map booking state. target=%s snippet=%s",
            target,
            normalized[:300],
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
