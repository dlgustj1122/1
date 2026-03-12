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


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
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

    interval = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    return watcher, interval


def main() -> None:
    setup_logging()
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
        try:
            watcher.notifier.send_message("종료됐습니다.")
        except Exception:  # noqa: BLE001
            LOGGER.exception("Failed to send shutdown notification")


if __name__ == "__main__":
    main()
