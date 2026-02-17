import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from backend_toolkit.logger import get_logger
from main import run as run_etl

logger = get_logger("scheduler")

IRAN = ZoneInfo("Asia/Tehran")

CHECK_INTERVAL_SECONDS = 60

ALLOWED_START_HOUR = 8   # inclusive
ALLOWED_END_HOUR = 19    # inclusive

last_run_minute: datetime | None = None


def validate_env() -> None:
    required_vars = [
        "SOURCE_DB",
        "TARGET_DB",
        "BT_MONGO_URI",
        "BT_MONGO_DB",
        "BT_MONGO_COLLECTION",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.critical(
            "missing required environment variables",
            extra={"missing_vars": missing},
        )
        raise RuntimeError(f"Missing env vars: {missing}")


def is_allowed_time(now: datetime) -> bool:
    return ALLOWED_START_HOUR <= now.hour <= ALLOWED_END_HOUR


def should_run(now: datetime) -> bool:
    global last_run_minute

    if not is_allowed_time(now):
        return False

    current_minute = now.replace(second=0, microsecond=0)

    if last_run_minute == current_minute:
        return False

    return True


def main() -> None:
    validate_env()

    while True:
        try:
            now = datetime.now(IRAN)

            if should_run(now):
                run_etl()

                global last_run_minute
                last_run_minute = now.replace(second=0, microsecond=0)
        except Exception as e:
            logger.exception("scheduler error",extra={"exception":e},)

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
