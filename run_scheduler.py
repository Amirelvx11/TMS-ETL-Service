import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from backend_toolkit.logger import get_logger
from tools.cleanup_duplicates import cleanup_duplicate_products
from main import run as run_etl

logger = get_logger("scheduler")

IRAN = ZoneInfo("Asia/Tehran")

CHECK_INTERVAL_SECONDS = 60

ALLOWED_START_HOUR = 8   # inclusive
ALLOWED_END_HOUR = 19    # inclusive

last_run_minute: datetime | None = None
last_cleanup_date: datetime.date | None = None


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


def should_run_cleanup(now: datetime) -> bool:
    global last_cleanup_date

    # if not is_allowed_time(now):
    #     return False
    
    # run once per day at 18:00
    if now.hour != 18 or now.minute != 0:
        return False

    today = now.date()

    if last_cleanup_date == today:
        return False

    return True


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
    
    logger.info(f"Scheduler started. Window: {ALLOWED_START_HOUR}:00 - {ALLOWED_END_HOUR}:59")
    while True:
        try:
            now = datetime.now(IRAN)

            if should_run(now):
                run_etl()
                global last_run_minute
                last_run_minute = now.replace(second=0, microsecond=0)

            if should_run_cleanup(now):
                cleanup_duplicate_products()

                global last_cleanup_date
                last_cleanup_date = now.date()

        except Exception:
            logger.exception("scheduler iteration failed")
            time.sleep(60)

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
