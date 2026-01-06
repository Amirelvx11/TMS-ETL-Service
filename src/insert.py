import uuid
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from backend_toolkit.logger import get_logger
from .config import dst_engine, USER_GUID

logger = get_logger("insert")


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
        logger.info(
            "products inserted",
            extra={"count": len(df)},
        )
        return len(df)
    except SQLAlchemyError:
        logger.exception("product insertion failed")
        return 0


def insert_guaranty(df_products: pd.DataFrame) -> int:
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
        logger.exception("error checking existing productIds for guaranty")
        return 0

    now = datetime.now()
    rows_to_insert = []

    for _, p in df_products.iterrows():
        if p["Id"] in existing_ids:
            continue

        start_date = p["ProductionDate"]
        if start_date is None:
            logger.warning(
                "Skipping guaranty due to NULL ProductionDate",
                extra={"product_id": p["Id"]},
            )
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
        logger.info(
            "guaranty inserted",
            extra={"count": len(rows_to_insert)},
        )
        return len(rows_to_insert)
    except SQLAlchemyError as e:
        logger.exception("guaranty insertion failed")
        return 0
