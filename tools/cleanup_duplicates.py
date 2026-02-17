from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.config import dst_engine
from backend_toolkit.logger import get_logger

logger = get_logger("cleanup-duplicates")

def cleanup_duplicate_products(lookback_hours: int = 336) -> int:
    sql = text("""
        DECLARE @cnt INT;
        EXEC mfu.usp_RemoveDuplicateProducts
            @LookbackHours = :hours,
            @DeletedCount = @cnt OUTPUT;
        SELECT @cnt AS deleted_count;
    """)
    try:
        with dst_engine.begin() as conn:
            deleted = conn.execute(sql, {"hours": lookback_hours}).scalar_one()

        if deleted > 0:
            logger.warning(
                "Duplicate cleanup removed %s records (lookback_hours=%s)",
                extra={
                    "deleted_counts":deleted,
                    "lookback_hours":lookback_hours,
                    },
            )

        return deleted
    except SQLAlchemyError:
        logger.exception("cleanup duplicate serials failed")
        return 0
