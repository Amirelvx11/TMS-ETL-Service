import pandas as pd
from sqlalchemy import text
from .config import src_engine, dst_engine


def get_last_tms_id():
    sql = text("SELECT ISNULL(MAX(TmsId), 0) FROM HamonDev.mfu.Product")
    with dst_engine.connect() as conn:
        last_id = conn.execute(sql).scalar()
    print(f"last Tms ID updated : {last_id}")
    return last_id


def fetch_lookup_maps():
    with dst_engine.connect() as conn:
        os_df = pd.read_sql("SELECT Id, Title FROM HamonDev.mfu.OperatingSystem", conn)
        mgr_df = pd.read_sql("SELECT Id, Title FROM HamonDev.mfu.Manager", conn)

    os_map = {str(r["Title"]).strip().upper(): r["Id"] for _, r in os_df.iterrows()}
    mgr_map = {str(r["Title"]).strip().upper(): r["Id"] for _, r in mgr_df.iterrows()}
    return os_map, mgr_map


def fetch_source_rows(last_id: int):
    sql = text("""
        SELECT id, sn, imei, libver, cosver, datetime
        FROM h_tool.tab_reader_barcode AS trb
        WHERE trb.id > :last_id
        ORDER BY trb.id ASC
    """)
    with src_engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"last_id": last_id})

    print(f"[OK] Retrieved {len(df)} new source rows after id={last_id}")
    return df
