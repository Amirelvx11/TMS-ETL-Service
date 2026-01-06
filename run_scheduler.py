import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from backend_toolkit.logger import get_logger
from backend_toolkit.utils.timezone import now_iran_str
from main import run as run_etl

logger = get_logger("scheduler")

IRAN = ZoneInfo("Asia/Tehran")
CHECK_INTERVAL_SECONDS = 60
ALLOWED_START = 8
ALLOWED_END = 20  # inclusive

last_run_hour = None


def validate_env() -> None:
    required_vars = [
        "SOURCE_DB",
        "BT_MONGO_URI",
        "BT_MONGO_DB",
        "BT_MONGO_COLLECTION",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.critical(
            "Missing required environment variables",
            extra={"missing_vars": missing},
        )
        raise RuntimeError(f"Missing env vars: {missing}")

    logger.info("Environment validation passed")


def should_run(now: datetime) -> bool:
    global last_run_hour

    if not (ALLOWED_START <= now.hour <= ALLOWED_END):
        return False

    if last_run_hour == now.hour:
        return False

    last_run_hour = now.hour
    return True


def main() -> None:
    validate_env()

    logger.info(
        "Scheduler started",
        extra={
            "timezone": "Asia/Tehran",
            "allowed_hours": f"{ALLOWED_START}-{ALLOWED_END}",
        },
    )

    while True:
        try:
            now = datetime.now(IRAN)

            if should_run(now):
                logger.info(
                    "Scheduler triggering ETL",
                    extra={"hour": now.hour},
                )
                run_etl()
        except Exception:
            logger.exception("Scheduler error")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
