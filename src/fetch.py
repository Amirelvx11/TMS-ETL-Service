import re
import uuid
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from backend_toolkit.logger import get_logger
from .config import src_engine, dst_engine, USER_GUID


logger = get_logger("fetch")


# ---------- HELPERS ----------

def normalize_os(value: str) -> str:
    if not value:
        return ""
    v = value.strip().upper()
    # Remove ONLY single trailing letter after digit (e.g. 7.6A → 7.6)
    return re.compile(r"(\d)([A-Z])$").sub(r"\1", v)


def manager_exact(value: str) -> str:
    return value.strip().upper() if value else ""


def manager_short(value: str) -> str:
    if not value:
        return ""
    v = value.strip().upper()
    return v[2:] if len(v) > 2 and v[:2].isalpha() else v


# ---------- VERSION ENSURE ----------


def ensure_version_exists_os(raw: str) -> str | None:
    """OS version checking.
    - if Version Title exist -> use that existing guid From Os Table
    - if not -> create & insert new version in OS Table
    """
    title = normalize_os(raw)
    if not title:
        return None

    sql_sel = "SELECT Id FROM Hamon.mfu.OperatingSystem WITH (NOLOCK) WHERE UPPER(Title) = :t"
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
        logger.warning(
                "Inserted new OS version.",
                extra={
                 "version": title,
                 "os_version_id": new_id,
                },
        )
        return new_id


def ensure_version_exists_manager(raw: str) -> str:
    """Manager insert logic: exact → short → insert exact."""
    exact = manager_exact(raw)
    short = manager_short(raw)

    sql_sel = """SELECT Id FROM Hamon.mfu.Manager WITH (NOLOCK) WHERE UPPER(Title) = :t"""

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
        logger.warning(
                "Inserted new Manager version.",
                extra={
                        "version": exact,
                        "manager_version_id": new_id,
                },
        )
        return new_id


def resolve_missing_versions(df, os_map, mgr_exact, mgr_short):
    for raw in df["cosver"].dropna().unique():
        key = normalize_os(raw)
        if key and key not in os_map:
            os_map[key] = ensure_version_exists_os(raw)

    for raw in df["libver"].dropna().unique():
        ex = manager_exact(raw)
        sh = manager_short(raw)
        if ex not in mgr_exact and sh not in mgr_short:
            new_id = ensure_version_exists_manager(raw)
            mgr_exact[ex] = new_id
            mgr_short[sh] = new_id


# ---------- FETCH ----------

def fetch_lookup_maps():
    "Get last os & manager versions from Target DB."
    try:
        with dst_engine.connect() as conn:
            os_df = pd.read_sql("SELECT Id, Title FROM Hamon.mfu.OperatingSystem WITH (NOLOCK)", conn)
            mgr_df = pd.read_sql("SELECT Id, Title FROM Hamon.mfu.Manager WITH (NOLOCK)", conn)

        os_map = {normalize_os(t): i for i, t in os_df.itertuples(index=False)}
        mgr_exact = {manager_exact(t): i for i, t in mgr_df.itertuples(index=False)}
        mgr_short = {manager_short(t): i for i, t in mgr_df.itertuples(index=False)}

        return os_map, mgr_exact, mgr_short
    except SQLAlchemyError:
        logger.exception("Lookup map fetch failed")
        return {}, {}, {}


def get_last_tms_id() -> int:
    "Fetch last updated Id on Target DB."
    try:
        with dst_engine.connect() as conn:
            val = conn.execute(text("SELECT ISNULL(MAX(TmsId), 0) FROM Hamon.mfu.Product WITH (NOLOCK)")).scalar_one()
            return int(val)
    except SQLAlchemyError as e:
        logger.exception("Failed to fetch last TmsId")
        return 0


def fetch_source_rows(last_id: int) -> pd.DataFrame:
    "Fetch Source DB records for new changes, you can adjust this based on your columns."
    sql = text("""
        SELECT id, tusn, sn, imei, libver, cosver, datetime
        FROM h_tool.tab_reader_barcode AS trb
        WHERE trb.id > :last_id
	AND trb.datetime <= (NOW() - INTERVAL 60 SECOND)
        ORDER BY trb.id ASC
    """)
    try:
        with src_engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"last_id": last_id})
        if len(df) > 0:
            logger.debug(
                "fetched source rows",
                extra={
                    "count": len(df),
                    "from_tms_id": last_id,
                },
            )
        return df
    except SQLAlchemyError as e:
        logger.exception("Failed to fetch source rows")
        return pd.DataFrame()
