from src.fetch import get_last_tms_id, fetch_lookup_maps, fetch_source_rows
from src.transform import transform_products
from src.insert import insert_products, insert_guaranty
from src.logger import get_logger

log = get_logger("main")

def run() -> int:
    """Main function to run the ETL pipeline."""
    try:
        last_id = get_last_tms_id()
        os_map, mgr_map = fetch_lookup_maps()

        df_src = fetch_source_rows(last_id)

        if df_src.empty:
            log.info("No new records to process.")
            return 0
        
        df_prod = transform_products(df_src, os_map, mgr_map)

        if df_prod.empty:
            log.info("No new records to process.")
            return 0

        inserted_products = insert_products(df_prod)
        inserted_guaranty = insert_guaranty(df_prod)

        if inserted_products == 0:
            log.info("No new records to process.")  # single-line policy
        else:
            max_tms = int(df_prod["TmsId"].max())
            log.info(f"Processed {inserted_products} products, {inserted_guaranty} guaranty rows. Updated through TmsId={max_tms}.")
        return 0
    except Exception as e:
        log.exception(f"ETL failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run())
