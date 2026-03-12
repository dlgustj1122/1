from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from cgv_watcher.models import WatchTarget
from cgv_watcher.notifier import TelegramNotifier
from cgv_watcher.parser import CGVParser
from cgv_watcher.scheduler import PollScheduler
from cgv_watcher.state_store import StateStore
from cgv_watcher.watcher import CGVBookingWatcher

LOGGER = logging.getLogger(__name__)
DEFAULT_CGV_URL = "https://www.cgv.co.kr/ticket/"


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def _sanitize_env_value(value: str) -> str:
    return value.replace("\\n", "").strip()


def _load_required_env(env_aliases: dict[str, list[str]]) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    missing: list[str] = []

    for canonical_key, aliases in env_aliases.items():
        found_value = ""
        for key in aliases:
            raw = os.getenv(key)
            if raw is None:
                continue
            sanitized = _sanitize_env_value(raw)
            if sanitized:
                found_value = sanitized
                break

        if found_value:
            values[canonical_key] = found_value
        else:
            missing.append(canonical_key)

    return values, missing


def load_env_or_raise() -> dict[str, str]:
    load_dotenv()

    env_aliases = {
        "CGV_MOVIE_NAME": ["CGV_MOVIE_NAME", "영화제목", "MOVIE_NAME"],
        "CGV_THEATER_NAME": ["CGV_THEATER_NAME", "THEATER_NAME"],
        "CGV_DATE": ["CGV_DATE", "DATE"],
        "TELEGRAM_BOT_TOKEN": ["TELEGRAM_BOT_TOKEN", "BOT_TOKEN"],
        "TELEGRAM_CHAT_ID": ["TELEGRAM_CHAT_ID", "CHAT_ID"],
    }

    values, missing = _load_required_env(env_aliases)

    cgv_url = _sanitize_env_value(os.getenv("CGV_URL", DEFAULT_CGV_URL))
    values["CGV_URL"] = cgv_url or DEFAULT_CGV_URL

    cgv_format = _sanitize_env_value(os.getenv("CGV_FORMAT", ""))
    values["CGV_FORMAT"] = cgv_format

    if missing:
        raise ValueError(
            "Missing required env vars: "
            f"{', '.join(missing)}\n"
            "Please create a .env file from .env.example and fill required values."
        )
def load_env_or_raise() -> dict[str, str]:
    load_dotenv()
    required_keys = [
        "CGV_URL",
        "CGV_MOVIE_NAME",
        "CGV_THEATER_NAME",
        "CGV_DATE",
        "CGV_FORMAT",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]

    values: dict[str, str] = {}
    missing: list[str] = []
    for key in required_keys:
        value = os.getenv(key)
        if value is None or not value.strip():
            missing.append(key)
        else:
            values[key] = value.strip()

    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    return values




def _poll_interval_or_default(raw_value: str | None, default: int = 60) -> int:
    if raw_value is None or not raw_value.strip():
        return default

    try:
        interval = int(raw_value.strip())
    except ValueError:
        LOGGER.warning("Invalid POLL_INTERVAL_SECONDS=%s; using default %s", raw_value, default)
        return default

    if interval <= 0:
        LOGGER.warning("POLL_INTERVAL_SECONDS must be positive; using default %s", default)
        return default

    return interval

def build_watcher() -> tuple[CGVBookingWatcher, int]:
    env = load_env_or_raise()

    target = WatchTarget.from_env(env)
    parser = CGVParser()
    notifier = TelegramNotifier(
        bot_token=env["TELEGRAM_BOT_TOKEN"],
        chat_id=env["TELEGRAM_CHAT_ID"],
    )
    state_store = StateStore(path=os.getenv("STATE_FILE", "watcher_state.json"))

    watcher = CGVBookingWatcher(
        parser=parser,
        notifier=notifier,
        state_store=state_store,
        target=target,
        cgv_url=env["CGV_URL"],
    )

    interval = _poll_interval_or_default(os.getenv("POLL_INTERVAL_SECONDS"), default=60)
    interval = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    return watcher, interval


def main() -> None:
    setup_logging()

    watcher: CGVBookingWatcher | None = None
    start_message_sent = False

    try:
        watcher, interval = build_watcher()
        scheduler = PollScheduler(interval_seconds=interval)

        watcher.notifier.send_message("시작됐습니다.")
        start_message_sent = True
        scheduler.run_forever(watcher.check_once)
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by user")
    except ValueError as error:
        LOGGER.error("Configuration error: %s", error)
    watcher, interval = build_watcher()
    scheduler = PollScheduler(interval_seconds=interval)
    try:
        watcher.notifier.send_message("시작됐습니다.")
        scheduler.run_forever(watcher.check_once)
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by user")
    except Exception:  # noqa: BLE001
        LOGGER.exception("Unhandled error while running watcher")
        raise
    finally:
        if watcher is not None and start_message_sent:
            try:
                watcher.notifier.send_message("종료됐습니다.")
            except Exception:  # noqa: BLE001
                LOGGER.exception("Failed to send shutdown notification")
        try:
            watcher.notifier.send_message("종료됐습니다.")
        except Exception:  # noqa: BLE001
            LOGGER.exception("Failed to send shutdown notification")


if __name__ == "__main__":
    main()
