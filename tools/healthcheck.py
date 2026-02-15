import os
import sys
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


IRAN = ZoneInfo("Asia/Tehran")

RUN_TIMES = (
    dt_time(9, 0),   # 09:00
    dt_time(19, 0),  # 19:00
)

RUN_TOLERANCE_MINUTES = 1  # cron / scheduler drift tolerance
HEALTH_WINDOW_MINUTES = 120


def should_run(now: datetime) -> bool:
    """
    Allow execution only at 09:00 or 19:00 (± tolerance).
    """
    for t in RUN_TIMES:
        scheduled = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        if abs((now - scheduled).total_seconds()) <= RUN_TOLERANCE_MINUTES * 60:
            return True
    return False


def main() -> None:
    now = datetime.now(IRAN)

    # ---- HARD TIME GATE ----
    if not should_run(now):
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

    # --- Mongo ---
    try:
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
    except Exception:
        sys.exit(1)

    base_query = {
        "app": os.environ["BT_APP_NAME"],
        "environment": os.environ["BT_ENVIRONMENT"],
        "timestamp": {"$gte": cutoff_str},
    }

    # ---- RECENT ACTIVITY CHECK ----
    last_log = col.find_one(
        base_query,
        sort=[("timestamp", -1)],
    )

    if not last_log:
        sys.exit(1)

    # ---- ERROR LOG CHECK ----
    error_log = col.find_one(
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
            "fetched","inserted","completed","finished",
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
        
    # ---- ALL CHECKS PASSED ----
    sys.exit(0)


if __name__ == "__main__":
    main()
