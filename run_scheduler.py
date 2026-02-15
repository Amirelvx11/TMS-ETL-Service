import os
import time
from datetime import datetime, date
from zoneinfo import ZoneInfo
from backend_toolkit.logger import get_logger
from main import run as run_etl

logger = get_logger("scheduler")

IRAN = ZoneInfo("Asia/Tehran")
CHECK_INTERVAL_SECONDS = 60
RUN_HOURS = {9, 19}

last_run: dict[int, date] = {}


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


def should_run(now: datetime) -> bool:
    today = now.date()
    hour = now.hour

    if hour not in RUN_HOURS:
        return False

    if last_run.get(hour) == today:
        return False

    return True


def main() -> None:
    validate_env()

    logger.info(
        "scheduler started",
        extra={
            "timezone": "Asia/Tehran",
            "run_hours": sorted(RUN_HOURS),
        },
    )

    while True:
        try:
            now = datetime.now(IRAN)

            if should_run(now):
                logger.info(
                    "scheduler triggering ETL",
                    extra={"time(hour)": now.hour},
                )
                run_etl()
                last_run[now.hour] = now.date()
        except Exception:
            logger.exception("scheduler error")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
