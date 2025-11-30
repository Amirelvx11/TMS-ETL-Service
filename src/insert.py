import uuid
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .config import dst_engine
from src.logger import get_logger

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
        log.info(f"Inserted {len(df)} rows into mfu.Product.")
        return len(df)
    except SQLAlchemyError as e:
        log.error(f"Error inserting products into destination: {e}")
        return 0

def insert_guaranty(df_products: pd.DataFrame):
    """Insert guaranty data into the destination database."""
    if df_products.empty:
        return 0

    product_ids = list(df_products["Id"])
    if not product_ids:
        return 0

    # Prepare the SQL query to check existing ProductIds
    placeholders = ", ".join([f":id{i}" for i in range(len(product_ids))])
    sql = f"""SELECT ProductId FROM mfu.Guaranty WHERE ProductId IN ({placeholders})"""
    params = {f"id{i}": pid for i, pid in enumerate(product_ids)}

    try:
        with dst_engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()
            existing_ids = {r[0] for r in rows}
    except SQLAlchemyError as e:
        log.error(f"Error checking existing ProductIds: {e}")
        return 0
    
    now = datetime.now()
    rows_to_insert = []

    for _, p in df_products.iterrows():
        if p["Id"] in existing_ids:
            continue 

        start_date = p["ProductionDate"]
        end_date = start_date + timedelta(days=30 * 19)
        
        rows_to_insert.append({
            "IsActive": 1,
            "Id": str(uuid.uuid4()).upper(),
            "CreatedBy": "79D7759E-918B-4B3E-92B6-9D32161BC232",
            "CreatedOn": now,
            "ModifiedBy": "79D7759E-918B-4B3E-92B6-9D32161BC232",
            "ModifiedOn": now,
            "OwnerId": "79D7759E-918B-4B3E-92B6-9D32161BC232",
            "DeviceId": p["Id"],
            "StartDate": start_date,
            "EndDate": end_date,
            "Cancellation": 0,
            "Description": None,
            "ProductId": p["Id"]
        })
        
    if rows_to_insert:
        try:
            pd.DataFrame(rows_to_insert).to_sql(
                name="Guaranty",
                schema="mfu",
                con=dst_engine,
                if_exists="append",
                index=False,
                chunksize=500
            )
            log.info(f"Inserted {len(rows_to_insert)} rows into mfu.Guaranty.")
        except SQLAlchemyError as e:
            log.error(f"Error inserting new guaranty data: {e}")
            return 0
        return len(rows_to_insert)
    else:
        log.info("No new guaranty rows needed.")
        return 0
    
