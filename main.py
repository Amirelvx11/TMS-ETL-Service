from src.fetch import get_last_tms_id, fetch_lookup_maps, fetch_source_rows
from src.transform import transform_products
from src.insert import insert_products, insert_guaranty


def run():
    last_id = get_last_tms_id()
    os_map, mgr_map = fetch_lookup_maps()

    df_src = fetch_source_rows(last_id)
    df_prod = transform_products(df_src, os_map, mgr_map)

    insert_products(df_prod)
    insert_guaranty(df_prod)

    if not df_prod.empty:
        print("[INFO] Updated until TmsId:", df_prod["TmsId"].max())


if __name__ == "__main__":
    run()
