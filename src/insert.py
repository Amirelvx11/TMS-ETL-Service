import pandas as pd
import datetime
import uuid
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
        print(f"[ERROR] Insert failed: {e}")
        raise


def insert_guaranty(df_products):
    if df_products.empty:
        return

    now = datetime.datetime.now()
    rows = []
    for _, p in df_products.iterrows():
        start_date = p["ProductionDate"]
        end_date = (start_date + datetime.timedelta(days=30*19)) if start_date else None

        rows.append({
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

    pd.DataFrame(rows).to_sql(
        name="Guaranty",
        schema="mfu",
        con=dst_engine,
        if_exists="append",
        index=False,
        chunksize=500,
        method=None
    )
