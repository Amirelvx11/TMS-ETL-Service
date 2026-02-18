from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.config import dst_engine, USER_GUID
from backend_toolkit.logger import get_logger

logger = get_logger("sync-hamta-code")

SQL = """
UPDATE p
SET
    p.HamtaCode  = h.Code,
    p.ModifiedOn = SYSDATETIME(),
    p.ModifiedBy = :user
FROM Hamon.mfu.Product p (NOLOCK)
JOIN Hamon.mfu.HamtaCode h (NOLOCK)
    ON p.SerialNumber = h.Serial
WHERE
    p.TmsId > :last_tms_id
    AND p.SerialNumber IS NOT NULL
    AND LTRIM(RTRIM(p.SerialNumber)) <> ''
    AND (
        p.HamtaCode IS NULL
        OR LTRIM(RTRIM(p.HamtaCode)) = ''
        OR p.HamtaCode <> h.Code
    );
"""

def sync_hamta_code(last_tms_id: int) -> int:
    """Updates HamtaCode for products inserted after 'last_tms_id'."""
    try:
        with dst_engine.begin() as conn:
            result = conn.execute(
                text(SQL),
                {
                    "last_tms_id": last_tms_id,
                    "user": USER_GUID,
                },
            )
            affected = result.rowcount or 0

        if affected > 0:
            logger.debug(
                "HamtaCode synced",
                extra={
                    "from_tms_id": last_tms_id,
                    "affected_rows": affected,
                },
            )

        return affected

    except SQLAlchemyError:
        logger.exception("HamtaCode sync failed")
        return 0
