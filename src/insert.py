import pandas as pd
import datetime
import uuid
from sqlalchemy import text
from .config import dst_engine


def insert_products(df: pd.DataFrame):
    if df.empty:
        print("[INFO] No new records to insert.")
        return

    try:   
        df.to_sql(
            name="Product",
            schema="mfu",
            con=dst_engine,
            if_exists="append",
            index=False,
            chunksize=500,
            method=None,
        )
        print(f"[OK] {len(df)} records inserted into mfu.Product.")
    except Exception as e:
        print(f"[ERROR] Product insert failed: {e}")
        raise


def insert_guaranty(df_products):
    if df_products.empty:
        print("[INFO] No guaranty needed.")
        return

    product_ids = list(df_products["Id"])
    placeholders = ", ".join([f":id{i}" for i in range(len(product_ids))])

    sql = f"""
        SELECT ProductId
        FROM mfu.Guaranty
        WHERE ProductId IN ({placeholders})
    """
    params = {f"id{i}": pid for i, pid in enumerate(product_ids)}

    with dst_engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()
        existing_ids = {r[0] for r in rows}

    now = datetime.datetime.now()
    rows_to_insert = []

    for _, p in df_products.iterrows():
        if p["Id"] in existing_ids:
            continue

        start_date = p["ProductionDate"]
        end_date = start_date + datetime.timedelta(days=30*19)

        rows_to_insert.append({
            "Id": str(uuid.uuid4()).upper(),
            "IsActive": 1,
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
        pd.DataFrame(rows_to_insert).to_sql(
            name="Guaranty",
            schema="mfu",
            con=dst_engine,
            if_exists="append",
            index=False,
            chunksize=500,
            method=None
        )
        print(f"[OK] {len(rows_to_insert)} records inserted into mfu.Guaranty.")
    else:
        print("[INFO] No new guaranty rows needed.")
        