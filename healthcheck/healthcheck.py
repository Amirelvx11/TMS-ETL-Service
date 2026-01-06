import os
import sys
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


IRAN = ZoneInfo("Asia/Tehran")

ALLOWED_START = dt_time(8, 0)
ALLOWED_END = dt_time(20, 0)

# Scheduler ticks every minute, ETL hourly
HEALTH_WINDOW_MINUTES = 120


def within_allowed_window(now: datetime) -> bool:
    """08:00 → 20:00 window"""
    return ALLOWED_START <= now.time() <= ALLOWED_END


def main() -> None:
    # --- ENV Validation ---
    REQUIRED = [
        "BT_MONGO_URI",
        "BT_MONGO_DB",
        "BT_MONGO_COLLECTION",
        "BT_APP_NAME",
        "BT_ENVIRONMENT",
        "SOURCE_DB",
        "TARGET_DB",
        "USER_GUID",
    ]

    for key in REQUIRED:
        if not os.getenv(key):
            sys.exit(1)

    now = datetime.now(IRAN)
    cutoff = now - timedelta(minutes=HEALTH_WINDOW_MINUTES)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    # --- Mongo ---
    client = MongoClient(
        os.environ["BT_MONGO_URI"],
        serverSelectionTimeoutMS=3000,
    )
    client.admin.command("ping")

    col = client[
        os.environ["BT_MONGO_DB"]
    ][
        os.environ["BT_MONGO_COLLECTION"]
    ]

    base_query = {
        "app": os.environ["BT_APP_NAME"],
        "environment": os.environ["BT_ENVIRONMENT"],
        "timestamp": {"$gte": cutoff_str},
    }

    # --- Recent activity (scheduler / ETL ran or ticked) ---
    last_log = col.find_one(
        base_query,
        sort=[("timestamp", -1)],
    )

    if within_allowed_window(now):
        if not last_log:
            sys.exit(1)
    else:
        pass

    # --- Error detection ---
    error_log = col.find_one(
        {
            **base_query,
            "level": {"$in": ["ERROR", "CRITICAL"]},
        }
    )
    if error_log:
        sys.exit(1)

    # --- Scheduler / ETL marker validation ---
    if last_log:
        msg = (last_log.get("message") or "").lower()

        HEALTHY_MARKERS = (
            "scheduler",
            "triggering",
            "started",
            "validation",
            "fetched",
            "inserted",
            "completed",
            "finished",
        )

        if not any(m in msg for m in HEALTHY_MARKERS):
            sys.exit(1)

    # --- DB Connection Check ---
    try:
        src_engine = create_engine(
            os.environ["SOURCE_DB"],
            pool_pre_ping=True,
            pool_timeout=3,
        )
        with src_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        dst_engine = create_engine(
            os.environ["TARGET_DB"],
            pool_pre_ping=True,
            pool_timeout=3,
        )
        with dst_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        sys.exit(1)
        

    sys.exit(0)


if __name__ == "__main__":
    main()
