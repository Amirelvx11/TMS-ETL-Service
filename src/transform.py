import uuid
import datetime
import pandas as pd


def transform_products(df, os_map, mgr_map):
    now = datetime.datetime.now()
    products = []

    for _, row in df.iterrows():
        sn = str(row.get("sn") or "").strip()

        # PartId rules
        if sn.startswith("00"):
            part_id = "A3925DD2-F7C3-4E27-B487-E547F8F980E2"
        elif sn.startswith("05"):
            part_id = "B159B8DA-AD61-4C25-97C8-C82CF7955D06"
        else:
            part_id = ""

        # IMEI parsing
        imei_str = str(row.get("imei") or "").strip()
        imei1, imei2 = "0", "0"

        if "," in imei_str:
            parts = [x.strip() for x in imei_str.split(",")]
            imei1 = parts[0] or "0"
            imei2 = parts[1] if len(parts) > 1 else "0"
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

    print(f"[OK] Transformed {len(products)} rows from h_tool.tab_reader_barcode for insert.")
    return pd.DataFrame(products)
