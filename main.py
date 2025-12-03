from src.fetch import get_last_tms_id, fetch_lookup_maps, fetch_source_rows
from src.transform import transform_products
from src.insert import insert_products, insert_guaranty
from src.logger import get_logger

log = get_logger("main")

def run():
    """Main function to run the ETL pipeline."""
    log.info("ETL cycle started.")

    last_id = get_last_tms_id()
    df_src = fetch_source_rows(last_id)

    if df_src.empty:
        log.info("No new rows found.")
        return
    
    os_map, mgr_exact, mgr_short = fetch_lookup_maps()
    df_prod = transform_products(df_src, os_map, mgr_exact, mgr_short)

    inserted = insert_products(df_prod)
    if inserted > 0:
        insert_guaranty(df_prod)

    log.info(f"ETL cycle completed. Processed {len(df_prod)} products.")

if __name__ == "__main__":
    run()
    