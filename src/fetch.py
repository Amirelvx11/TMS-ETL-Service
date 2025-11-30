import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .config import src_engine, dst_engine
from src.logger import get_logger

log = get_logger("fetch")

def get_last_tms_id() -> int:
    """Fetch the last TmsId from the destination database."""
    sql = text("SELECT ISNULL(MAX(TmsId), 0) FROM HamonDev.mfu.Product")
    try:
        with dst_engine.connect() as conn:
            last_id = conn.execute(sql).scalar_one()
        log.info(f"Last TmsId from destination: {last_id}")
        return int(last_id)
    except SQLAlchemyError as e:
        log.error(f"Error occurred while fetching last TmsId: {e}")
        return 0

def fetch_lookup_maps():
    """Fetch lookup maps for OS and Manager from the destination DB."""
    try:
        with dst_engine.connect() as conn:
            os_df = pd.read_sql("SELECT Id, Title FROM HamonDev.mfu.OperatingSystem", conn)
            mgr_df = pd.read_sql("SELECT Id, Title FROM HamonDev.mfu.Manager", conn)

        os_map = {str(r["Title"]).strip().upper(): r["Id"] for _, r in os_df.iterrows()}
        mgr_map = {str(r["Title"]).strip().upper(): r["Id"] for _, r in mgr_df.iterrows()}
        
        return os_map, mgr_map
    except SQLAlchemyError as e:
        log.error(f"Error occurred while fetching lookup maps: {e}")
        return {}, {}

def fetch_source_rows(last_id: int) -> pd.DataFrame:
    """Fetch new rows from the source database based on the last TmsId."""
    sql = text("""
        SELECT id, sn, imei, libver, cosver, datetime
        FROM h_tool.tab_reader_barcode AS trb
        WHERE trb.id > :last_id
        ORDER BY trb.id ASC
    """)
    try:
        with src_engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"last_id": last_id})
        log.info(f"Fetched {len(df)} rows from source with last_id={last_id}")
        return df
    except SQLAlchemyError as e:
        log.error(f"Error occurred while fetching rows from source: {e}")
        return pd.DataFrame()
