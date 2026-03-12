from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BookingState(str, Enum):
    UNAVAILABLE = "unavailable"
    PREPARING = "preparing"
    AVAILABLE = "available"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class WatchTarget:
    movie_name: str
    theater_name: str
    date: str
    movie_format: str

    def to_dict(self) -> dict[str, str]:
        return {
            "movie_name": self.movie_name,
            "theater_name": self.theater_name,
            "date": self.date,
            "movie_format": self.movie_format,
        }

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "WatchTarget":
        return cls(
            movie_name=env["CGV_MOVIE_NAME"],
            theater_name=env["CGV_THEATER_NAME"],
            date=env["CGV_DATE"],
            movie_format=env["CGV_FORMAT"],
        )
