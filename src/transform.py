import uuid
from datetime import datetime
import pandas as pd
from src.logger import get_logger

log = get_logger("transform")

def transform_products(df: pd.DataFrame, os_map: dict, mgr_map: dict) -> pd.DataFrame:
    """Transform source rows into the product format."""
    if df.empty:
        log.info("No data to transform.")
        return pd.DataFrame(columns=[
            "IsActive", "Id", "CreatedBy", "CreatedOn", "ModifiedBy", "ModifiedOn", "OwnerId",
            "PartId", "IMEI1", "IMEI2", "HamtaCode", "ProductionDate", "OsVersionId", "ManagerVersionId",
            "SerialNumber", "TmsId"
        ])

    now = datetime.now()
    products = []

    for _, row in df.iterrows():
        sn = str(row.get("sn") or "").strip()

        # PartId rules
        part_id = ""
        if sn.startswith("00"):
            part_id = "A3925DD2-F7C3-4E27-B487-E547F8F980E2"
        elif sn.startswith("05"):
            part_id = "B159B8DA-AD61-4C25-97C8-C82CF7955D06"

        # IMEI parsing
        imei_str = str(row.get("imei") or "").strip()
        imei1, imei2 = "0", "0"
        if "," in imei_str:
            parts = [x.strip() for x in imei_str.split(",")]
            imei1, imei2 = parts[0], parts[1] if len(parts) > 1 else "0"
        elif imei_str.isdigit():
            imei1 = imei_str

        os_id = os_map.get(str(row.get("cosver") or "").strip().upper())
        mgr_id = mgr_map.get(str(row.get("libver") or "").strip().upper())

        prod_date = pd.to_datetime(row.get("datetime"), errors="coerce")
        prod_date_val = prod_date.date() if pd.notna(prod_date) else None

        products.append({
            "Id": str(uuid.uuid4()).upper(),
            "IsActive": 1,
            "CreatedBy": "79D7759E-918B-4B3E-92B6-9D32161BC232",
            "CreatedOn": now,
            "ModifiedBy": "79D7759E-918B-4B3E-92B6-9D32161BC232",
            "ModifiedOn": now,
            "OwnerId": "79D7759E-918B-4B3E-92B6-9D32161BC232",
            "PartId": part_id,
            "IMEI1": imei1,
            "IMEI2": imei2,
            "HamtaCode": "",
            "ProductionDate": prod_date_val,
            "OsVersionId": os_id,
            "ManagerVersionId": mgr_id,
            "SerialNumber": sn,
            "TmsId": int(row["id"]),
        })

    log.info(f"Transformed {len(products)} rows.")
    return pd.DataFrame(products)
