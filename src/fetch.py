import re
import uuid
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .logger import get_logger
from .config import src_engine, dst_engine, USER_GUID

log = get_logger("fetch")

def normalize_os(value: str) -> str:
    if not value:
        return ""
    value = value.strip().upper()
    return re.sub(r"[A-Z]$", "", value)

def manager_exact(value: str) -> str:
    return value.strip().upper()

def manager_short(value: str) -> str:
    v = value.strip().upper()
    return v[2:] if len(v) > 2 and v[:2].isalpha() else v

def ensure_version_exists_os(raw: str) -> str:
    title = normalize_os(raw)
    if not title:
        return None

    sql_sel = """SELECT Id FROM Hamon.mfu.OperatingSystem WHERE UPPER(Title) = :t"""
    with dst_engine.begin() as conn:
        row = conn.execute(text(sql_sel), {"t": title}).fetchone()
        if row:
            return row[0]

        new_id = str(uuid.uuid4()).upper()
        sql_ins = """
            INSERT INTO Hamon.mfu.OperatingSystem
            (Id, Title, IsActive, CreatedBy, CreatedOn, ModifiedBy, ModifiedOn, OwnerId, Description)
            VALUES (:id, :title, 1, :u, GETDATE(), :u, GETDATE(), :u, NULL)
        """
        conn.execute(text(sql_ins), {"id": new_id, "title": title, "u": USER_GUID})
        log.info(f"Inserted new OS version: {title} ({new_id})")
        return new_id
    
def ensure_version_exists_manager(raw: str) -> str:
    """Manager insert logic: exact → short → insert exact."""
    exact = manager_exact(raw)
    short = manager_short(raw)

    sql_sel = """SELECT Id FROM Hamon.mfu.Manager WHERE UPPER(Title) = :t"""

    with dst_engine.begin() as conn:
        r1 = conn.execute(text(sql_sel), {"t": exact}).fetchone()
        if r1:
            return r1[0]

        r2 = conn.execute(text(sql_sel), {"t": short}).fetchone()
        if r2:
            return r2[0]

        new_id = str(uuid.uuid4()).upper()
        sql_ins = """
            INSERT INTO Hamon.mfu.Manager
            (Id, Title, IsActive, CreatedBy, CreatedOn, ModifiedBy, ModifiedOn, OwnerId, Description)
            VALUES (:id, :title, 1, :u, GETDATE(), :u, GETDATE(), :u, NULL)
        """
        conn.execute(text(sql_ins), {"id": new_id, "title": exact, "u": USER_GUID})
        log.info(f"Inserted new Manager version: {exact} ({new_id})")
        return new_id

def fetch_lookup_maps():
    try:
        with dst_engine.connect() as conn:
            os_df = pd.read_sql("SELECT Id, Title FROM Hamon.mfu.OperatingSystem WITH (NOLOCK)", conn)
            mgr_df = pd.read_sql("SELECT Id, Title FROM Hamon.mfu.Manager WITH (NOLOCK)", conn)

        os_map = {normalize_os(r["Title"]): r["Id"] for _, r in os_df.iterrows()}
        mgr_exact  = {manager_exact(r["Title"]): r["Id"] for _, r in mgr_df.iterrows()}
        mgr_short  = {manager_short(r["Title"]): r["Id"] for _, r in mgr_df.iterrows()}

        return os_map, mgr_exact, mgr_short
    
    except SQLAlchemyError as e:
        log.error(f"fetch_lookup_maps error: {e}")
        return {}, {}, {}

def get_last_tms_id() -> int:
    try:
        with dst_engine.connect() as conn:
            val = conn.execute(text("SELECT ISNULL(MAX(TmsId), 0) FROM Hamon.mfu.Product WITH (NOLOCK)")).scalar_one()
            return int(val)
    except SQLAlchemyError as e:
        log.error(f"Error occurred while getting last TmsId: {e}")
        return 0

def fetch_source_rows(last_id: int) -> pd.DataFrame:
    sql = text("""
        SELECT id, sn, imei, libver, cosver, datetime
        FROM h_tool.tab_reader_barcode AS trb
        WHERE trb.id > :last_id
        ORDER BY trb.id ASC
    """)
    try:
        with src_engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"last_id": last_id})
        if len(df) > 0:
            log.info(f"Fetched {len(df)} rows from source with last_id={last_id}")
        return df
    except SQLAlchemyError as e:
        log.error(f"Error occurred while fetching rows from source: {e}")
        return pd.DataFrame()
    
