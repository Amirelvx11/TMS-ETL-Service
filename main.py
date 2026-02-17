import time
from src.fetch import (
    get_last_tms_id, fetch_lookup_maps,
    resolve_missing_versions, fetch_source_rows
)
from src.transform import transform_products
from src.insert import insert_products, insert_guaranty
from tools.sync_hamta_code import sync_hamta_code
from tools.cleanup_duplicates import cleanup_duplicate_products
from backend_toolkit.logger import get_logger

logger = get_logger("main-etl")


def run():
    """Main function to run the ETL pipeline."""
    try:
        start_ts = time.monotonic()
        cleanup_duplicate_products()
        start_last_id = get_last_tms_id()

        df_src = fetch_source_rows(start_last_id)
        if df_src.empty:
            return

        os_map, mgr_exact, mgr_short = fetch_lookup_maps()
        resolve_missing_versions(df_src, 
                                 os_map, mgr_exact, mgr_short)
        df_prod = transform_products(df_src, os_map, mgr_exact, mgr_short)

        inserted_products = insert_products(df_prod)
        inserted_guaranty = insert_guaranty(df_prod) if inserted_products else 0

        hamta_synced = 0
        if inserted_products > 0:
            hamta_synced = sync_hamta_code(start_last_id)

        duration = round(time.monotonic() - start_ts, 3)

        logger.info(
            "ETL cycle completed",
            extra={
                "start_tms_id": start_last_id,
                "last_tms_id": int(df_prod["TmsId"].max()) if not df_prod.empty else start_last_id,
                "fetched": len(df_src),
                "inserted_products": inserted_products,
                "inserted_guaranty": inserted_guaranty,
                "hamta_synced": hamta_synced,
                "duration_sec": duration,
            },
        )
    except Exception as e:
        logger.critical("main etl cycle crashed",exc_info=True)
        raise


if __name__ == "__main__":
    run()
