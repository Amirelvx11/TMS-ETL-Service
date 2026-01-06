import time
from src.fetch import get_last_tms_id, fetch_lookup_maps, fetch_source_rows
from src.transform import transform_products
from src.insert import insert_products, insert_guaranty
from backend_toolkit.logger import get_logger

logger = get_logger("etl")

def run():
    """Main function to run the ETL pipeline."""
    try:
        start_ts = time.monotonic()

        start_last_id = get_last_tms_id()
        logger.info(
            "ETL cycle started",
            extra={"start_tms_id": start_last_id},
        )
        
        df_src = fetch_source_rows(start_last_id)
        if df_src.empty:
            logger.info(
                "ETL cycle finished - no new data",
                extra={"start_tms_id": start_last_id},
            )
            return

        os_map, mgr_exact, mgr_short = fetch_lookup_maps()
        df_prod = transform_products(df_src, os_map, mgr_exact, mgr_short)

        inserted_products = insert_products(df_prod)
        inserted_guaranty = insert_guaranty(df_prod) if inserted_products else 0

        duration = round(time.monotonic() - start_ts, 3)

        logger.info(
            "ETL cycle completed",
            extra={
                "start_tms_id": start_last_id,
                "last_tms_id": int(df_prod["TmsId"].max()),
                "fetched": len(df_src),
                "inserted_products": inserted_products,
                "inserted_guaranty": inserted_guaranty,
                "duration_sec": duration,
            },
        )
    except Exception as e:
        logger.critical("main etl cycle error")
        raise 

if __name__ == "__main__":
    run()
