import uuid
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from backend_toolkit.logger import get_logger
from .config import dst_engine, USER_GUID

log = get_logger("insert")

def insert_products(df: pd.DataFrame) -> int:
    """Insert transformed product rows into the destination database."""
    if df.empty:
        return 0

    try:
        with dst_engine.begin() as conn:
            df.to_sql(
                name="Product",
                schema="mfu",
                con=conn,
                if_exists="append",
                index=False,
                chunksize=500
            )
        log.info(f"Inserted {len(df)} rows into products.")
        return len(df)
    except SQLAlchemyError as e:
        log.error(f"Error inserting products into destination: {e}")
        return 0

def insert_guaranty(df_products: pd.DataFrame):
    """Insert guaranty data into the destination database."""
    if df_products.empty:
        return 0

    product_ids = list(df_products["Id"])
    existing_ids = set()
    batch_size = 2000  # MSSQL max = 2100 params

    try:
        with dst_engine.connect() as conn:
            for i in range(0, len(product_ids), batch_size):
                batch = product_ids[i:i+batch_size]
                params = {f"id{k}": v for k, v in enumerate(batch)}
                ph = ",".join([f":id{k}" for k in range(len(batch))])
                sql = f"SELECT ProductId FROM mfu.Guaranty WHERE ProductId IN ({ph})"
                rows = conn.execute(text(sql), params).fetchall()
                existing_ids.update(r[0] for r in rows)
    except SQLAlchemyError as e:
        log.error(f"Error checking existing ProductIds for guaranty: {e}")
        return 0

    now = datetime.now()
    rows_to_insert = []

    for _, p in df_products.iterrows():
        if p["Id"] in existing_ids:
            continue

        start_date = p["ProductionDate"]
        if start_date is None:
            log.warning(f"Skipping guaranty: Product {p['Id']} has NULL ProductionDate")
            continue

        end_date = start_date + timedelta(days=30 * 19)

        rows_to_insert.append({
            "IsActive": 1,
            "Id": str(uuid.uuid4()).upper(),
            "CreatedBy": USER_GUID,
            "CreatedOn": now,
            "ModifiedBy": USER_GUID,
            "ModifiedOn": now,
            "OwnerId": USER_GUID,
            "DeviceId": p["Id"],
            "StartDate": start_date,
            "EndDate": end_date,
            "Cancellation": 0,
            "Description": None,
            "ProductId": p["Id"]
        })

    if not rows_to_insert:
        log.info("No new guaranty rows required.")
        return 0

    try:
        pd.DataFrame(rows_to_insert).to_sql(
            name="Guaranty",
            schema="mfu",
            con=dst_engine,
            if_exists="append",
            index=False,
            chunksize=500
        )
        log.info(f"Inserted {len(rows_to_insert)} rows into guaranty.")
        return len(rows_to_insert)
    except SQLAlchemyError as e:
        log.error(f"Error inserting new guaranty data: {e}")
        return 0
    