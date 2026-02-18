import uuid
import pandas as pd
from datetime import datetime
from backend_toolkit.logger import get_logger
from .config import USER_GUID
from .fetch import normalize_os, manager_exact, manager_short, is_complete_row

logger = get_logger("transform")


def transform_products(df: pd.DataFrame, os_map, mgr_exact, mgr_short) -> pd.DataFrame | None:
    """Transform source rows into the product format."""
    if df.empty:
        return pd.DataFrame()

    invalid_rows = [r.id for r in df.itertuples(index=False) if not is_complete_row(r)]

    if invalid_rows:
        logger.warning(
            "incomplete rows detected – deferring batch",
            extra={
                "count": len(invalid_rows),
                "sample_ids": invalid_rows[:5],
            },
        )
        return None

    now = datetime.now()
    default_date = now.date()
    products = []

    for r in df.itertuples(index=False):
        sn = (r.sn or "").strip()
        tusn = (r.tusn or "").strip()
        
        part_id = ""
        if sn.startswith("00"):
            part_id = "A3925DD2-F7C3-4E27-B487-E547F8F980E2"
        elif sn.startswith("05"):
            part_id = "B159B8DA-AD61-4C25-97C8-C82CF7955D06"

        imei1, imei2 = "0", "0"
        imei_raw = (r.imei or "").strip()
        if "," in imei_raw:
            p = imei_raw.split(",")
            imei1, imei2 = p[0].strip(), p[1].strip() if len(p) > 1 else "0"
        elif imei_raw.isdigit():
            imei1, imei2 = imei_raw, "0"

        os_id = os_map.get(normalize_os(r.cosver))

        mgr_id = mgr_exact.get(manager_exact(r.libver)) or mgr_short.get(manager_short(r.libver))


        prod_dt = pd.to_datetime(r.datetime, errors="coerce")
        prod_date = prod_dt.date() if pd.notna(prod_dt) else default_date

        products.append({
            "Id": str(uuid.uuid4()).upper(),
            "IsActive": 1,
            "CreatedBy": USER_GUID,
            "CreatedOn": now,
            "ModifiedBy": USER_GUID,
            "ModifiedOn": now,
            "OwnerId": USER_GUID,
            "PartId": part_id,
            "IMEI1": imei1,
            "IMEI2": imei2,
            "HamtaCode": "", # Will be filled by sync_hamta_code later
            "ProductionDate": prod_date,
            "OsVersionId": os_id,
            "ManagerVersionId": mgr_id,
            "SerialNumber": sn,
            "TmsId": int(r.id),
            "Tusn": tusn,
        })

    logger.debug(
        "transformation completed",
        extra={"rows": len(products)},
    )
    return pd.DataFrame(products)
