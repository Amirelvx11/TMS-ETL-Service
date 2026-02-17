import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


IRAN = ZoneInfo("Asia/Tehran")

ALLOWED_START_HOUR = 8
ALLOWED_END_HOUR = 19

HEALTH_WINDOW_MINUTES = 5  # last 5 minutes of ETL activity


def is_inside_window(now: datetime) -> bool:
    return ALLOWED_START_HOUR <= now.hour <= ALLOWED_END_HOUR


def main() -> None:
    now = datetime.now(IRAN)

    # ---- TIME GATE ----
    if not is_inside_window(now):
        sys.exit(0)

    cutoff = now - timedelta(minutes=HEALTH_WINDOW_MINUTES)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    # --- ENV Validation ---
    REQUIRED = [
        "SOURCE_DB",
        "TARGET_DB",
        "USER_GUID",
        "BT_MONGO_URI",
        "BT_MONGO_DB",
        "BT_MONGO_COLLECTION",
        "BT_APP_NAME",
        "BT_ENVIRONMENT",
    ]

    for key in REQUIRED:
        if not os.getenv(key):
            sys.exit(1)

    # --- Mongo CONNECTIVITY ---
    try:
        client = MongoClient(
            os.environ["BT_MONGO_URI"],
            serverSelectionTimeoutMS=3000,
        )
        client.admin.command("ping")

        collection = client[
            os.environ["BT_MONGO_DB"]
        ][
            os.environ["BT_MONGO_COLLECTION"]
        ]
    except Exception:
        sys.exit(1)

    base_query = {
        "app": os.environ["BT_APP_NAME"],
        "environment": os.environ["BT_ENVIRONMENT"],
        "timestamp": {"$gte": cutoff_str},
    }

    # ---- RECENT ACTIVITY CHECK ----
    last_log = collection.find_one(
        base_query,
        sort=[("timestamp", -1)],
    )

    if not last_log:
        sys.exit(1)

    # ---- ERROR LOG CHECK ----
    error_log = collection.find_one(
        {
            **base_query,
            "level": {"$in": ("ERROR", "CRITICAL")},
        }
    )
    if error_log:
        sys.exit(1)

    # --- Scheduler / ETL marker validation ---
    if last_log:
        msg = (last_log.get("message") or "").lower()

        HEALTHY_MARKERS = (
            "scheduler","triggering","started","validation",
            "running","fetched","inserted","completed","finished",
        )

        if not any(m in msg for m in HEALTHY_MARKERS):
            sys.exit(1)

    # --- DB CONNECTIVITY ---
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

    # ---- ALL CHECKS PASSED ----
    sys.exit(0)


if __name__ == "__main__":
    main()
