import uuid
import pandas as pd
from datetime import datetime
from backend_toolkit.logger import get_logger
from .config import USER_GUID
from .fetch import (
    normalize_os,
    manager_exact,
    manager_short,
    ensure_version_exists_os,
    ensure_version_exists_manager,
)

logger = get_logger("transform")

def transform_products(df, os_map, mgr_map_exact, mgr_map_short):
    """Transform source rows into the product format."""
    if df.empty:
        return pd.DataFrame()

    now = datetime.now()
    products = []

    for _, row in df.iterrows():

        # Serial Number
        sn = str(row.get("sn") or "").strip()

        # tusn (complete number of serial number)
        tusn = str(row.get("tusn") or "").strip()

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

        # OS ID
        cos_raw = str(row.get("cosver") or "")
        cos_norm = normalize_os(cos_raw)
        os_id = os_map.get(cos_norm)
        if not os_id:
            os_id = ensure_version_exists_os(cos_raw)
            if os_id:
                os_map[cos_norm] = os_id

        # Manager ID
        lib_raw = str(row.get("libver") or "")
        ex = manager_exact(lib_raw)
        sh = manager_short(lib_raw)

        mgr_id = mgr_map_exact.get(ex) or mgr_map_short.get(sh)
        if not mgr_id:
            mgr_id = ensure_version_exists_manager(lib_raw)
            mgr_map_exact[ex] = mgr_id
            mgr_map_short[sh] = mgr_id

        prod_date = pd.to_datetime(row.get("datetime"), errors="coerce")
        prod_date_val = prod_date.date() if pd.notna(prod_date) else None

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
            "HamtaCode": "",
            "ProductionDate": prod_date_val,
            "OsVersionId": os_id,
            "ManagerVersionId": mgr_id,
            "SerialNumber": sn,
            "TmsId": int(row["id"]),
            "Tusn": tusn,
        })

    logger.debug(
        "transformation completed",
        extra={"rows": len(products)},
    )
    return pd.DataFrame(products)
