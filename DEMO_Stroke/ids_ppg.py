import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

def normalize_windows_path(p: str) -> str:
    if os.name == "nt" and p.startswith("/") and ":/" in p[:4]:
        return p[1:]
    return p

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = str(BASE_DIR / "device_wear_health_export.csv")
DEFAULT_OUTPUT_DIR = str(BASE_DIR / "output")
DEFAULT_MODULE_DIR = str(BASE_DIR)

DEFAULT_MONGO_CONFIG = {
    "host": "mongoreplica29ed1d62f12a1.mongodb.cn-beijing.volces.com",
    "port": 3717,
    "username": "apps-wr",
    "password": "eEcc7U!nNM3ivzC^f",
    "database": "andun_1",
    "collection": "device_collect_compress_data",
}

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--module-dir", default=DEFAULT_MODULE_DIR)
    parser.add_argument("--mongo-host", default=DEFAULT_MONGO_CONFIG["host"])
    parser.add_argument("--mongo-port", type=int, default=DEFAULT_MONGO_CONFIG["port"])
    parser.add_argument("--mongo-username", default=DEFAULT_MONGO_CONFIG["username"])
    parser.add_argument("--mongo-password", default=DEFAULT_MONGO_CONFIG["password"])
    parser.add_argument("--mongo-database", default=DEFAULT_MONGO_CONFIG["database"])
    parser.add_argument("--mongo-collection", default=DEFAULT_MONGO_CONFIG["collection"])
    parser.add_argument("--max-per-device", type=int, default=200)
    parser.add_argument("--date-from", default=None)
    parser.add_argument("--date-to", default=None)
    return parser.parse_args()

def ensure_module_import(module_dir: str) -> None:
    module_dir = normalize_windows_path(module_dir)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

def load_device_ids_from_csv(csv_path: str) -> List[str]:
    p = normalize_windows_path(csv_path)
    ids: List[str] = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return []
        header = [h.lstrip("\ufeff").strip() for h in header]
        try:
            idx = header.index("device_id")
        except ValueError:
            return []
        seen = set()
        for row in reader:
            if idx < len(row):
                val = str(row[idx]).strip()
                if val and val not in seen:
                    seen.add(val)
                    ids.append(val)
    return ids

def to_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            if value > 10000000000:
                return datetime.fromtimestamp(value / 1000.0)
            return datetime.fromtimestamp(value)
        except Exception:
            return None
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                continue
        return None
    return None

def format_dt(dt: Optional[datetime], with_micro: bool = False) -> Optional[str]:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f" if with_micro else "%Y-%m-%d %H:%M:%S")

def to_beijing(dt: Optional[datetime]) -> Optional[datetime]:
    return dt + timedelta(hours=8) if dt else None

def connect_mongo(cfg: Dict[str, Any]):
    from pymongo import MongoClient
    client = MongoClient(
        host=cfg.get("host"),
        port=int(cfg.get("port", 27017)),
        username=cfg.get("username"),
        password=cfg.get("password"),
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
    )
    _ = client.admin.command("ping")
    db = client[cfg.get("database")]
    coll = db[cfg.get("collection")]
    return client, coll

def build_time_filter(date_from: Optional[str], date_to: Optional[str]) -> Dict[str, Any]:
    flt: Dict[str, Any] = {}
    df = to_datetime(date_from) if date_from else None
    dt_ = to_datetime(date_to) if date_to else None
    if df and dt_:
        flt["collectTime"] = {"$gte": df, "$lte": dt_}
    elif df:
        flt["collectTime"] = {"$gte": df}
    elif dt_:
        flt["collectTime"] = {"$lte": dt_}
    return flt

def fetch_records_for_device(
    coll,
    device_id: str,
    max_per_device: int,
    date_from: Optional[str],
    date_to: Optional[str],
) -> List[Dict[str, Any]]:
    base_filter: Dict[str, Any] = {"deviceId": device_id}
    time_filter = build_time_filter(date_from, date_to)
    if time_filter:
        base_filter.update(time_filter)
    cursor = (
        coll.find(base_filter, projection={
            "deviceId": 1,
            "collectTime": 1,
            "createTime": 1,
            "collectData": 1,
            "wear_user_id": 1,
            "wearUserId": 1,
        })
        .sort([("collectTime", 1)])
        .limit(max_per_device)
    )
    return list(cursor)

def extract_bytes(data: Any) -> Optional[bytes]:
    try:
        if data is None:
            return None
        if isinstance(data, bytes):
            return data
        if isinstance(data, bytearray):
            return bytes(data)
        try:
            return bytes(data)
        except Exception:
            return None
    except Exception:
        return None

def decompress_and_build_entries(
    rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int, int, Optional[str]]:
    res_list: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []
    for r in rows:
        cbytes = extract_bytes(r.get("collectData"))
        ctime = to_datetime(r.get("collectTime"))
        if cbytes and ctime:
            res_list.append({
                "collectTime": format_dt(ctime, with_micro=False),
                "collectData": cbytes,
            })
            valid_rows.append(r)
    collect_count = len(res_list)
    wear_user_id = None
    if rows:
        first = rows[0]
        wear_user_id = first.get("wear_user_id") or first.get("wearUserId")
    if collect_count == 0:
        return [], 0, 0, wear_user_id
    from decompressed_comp_ppg_data import (
        get_compression_byte_data,
        check_bytes_compress_data,
        check_compression_data,
        uncompression_and_check_data,
        uncompress_data_upsample,
    )
    try:
        compression_data_bytes_list = get_compression_byte_data(res_list)
        compression_data_int_list = check_bytes_compress_data(compression_data_bytes_list)
        idx_map: List[int] = []
        filtered_int_list: List[List[int]] = []
        filtered_rows: List[Dict[str, Any]] = []
        for idx, item in enumerate(compression_data_int_list):
            if item is not None:
                idx_map.append(idx)
                filtered_int_list.append(item)
                filtered_rows.append(valid_rows[idx])
        if not filtered_int_list:
            return [], 0, collect_count, wear_user_id
        _ = check_compression_data(filtered_int_list)
        origin_ppg_data_list, hz_list = uncompression_and_check_data(filtered_int_list, request_tag="")
        upsampled_data_list = uncompress_data_upsample(origin_ppg_data_list, target_fs=250, rates=hz_list)
        processed_entries: List[Dict[str, Any]] = []
        for i, (orig, upsampled, row) in enumerate(zip(origin_ppg_data_list, upsampled_data_list, filtered_rows)):
            ctime = to_datetime(row.get("collectTime"))
            crtime = to_datetime(row.get("createTime"))
            ctime_bj = to_beijing(ctime)
            crtime_bj = to_beijing(crtime)
            processed_entries.append({
                "index": i,
                "collectTime": format_dt(ctime, with_micro=False),
                "createTime": format_dt(crtime, with_micro=True),
                "collectTime_beijing": format_dt(ctime_bj, with_micro=False),
                "createTime_beijing": format_dt(crtime_bj, with_micro=False),
                "originalDataSize": len(orig) if isinstance(orig, list) else 0,
                "decompressedData": upsampled if isinstance(upsampled, list) else [],
            })
        return processed_entries, len(processed_entries), collect_count, wear_user_id
    except Exception:
        processed_entries: List[Dict[str, Any]] = []
        for i, row in enumerate(valid_rows):
            ctime = to_datetime(row.get("collectTime"))
            crtime = to_datetime(row.get("createTime"))
            ctime_bj = to_beijing(ctime)
            crtime_bj = to_beijing(crtime)
            processed_entries.append({
                "index": i,
                "collectTime": format_dt(ctime, with_micro=False),
                "createTime": format_dt(crtime, with_micro=True),
                "collectTime_beijing": format_dt(ctime_bj, with_micro=False),
                "createTime_beijing": format_dt(crtime_bj, with_micro=False),
                "originalDataSize": 0,
                "decompressedData": [],
            })
        return processed_entries, len(processed_entries), collect_count, wear_user_id

def write_device_json(
    output_dir: str,
    device_id: str,
    wear_user_id: Optional[str],
    processed_entries: List[Dict[str, Any]],
    data_count: int,
    collect_count: int,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    now = datetime.now()
    fname = f"{device_id}_{now.strftime('%Y%m%d_%H%M%S')}.json"
    fpath = os.path.join(output_dir, fname)
    payload: Dict[str, Any] = {
        "deviceId": device_id,
        "wear_user_id": wear_user_id,
        "dataCount": data_count,
        "collectDataCount": collect_count,
        "processedData": processed_entries,
    }
    with open(fpath, "w", encoding="utf-8") as wf:
        json.dump(payload, wf, ensure_ascii=False)
    return fpath

def main():
    args = _parse_args()
    ensure_module_import(args.module_dir)
    device_ids = load_device_ids_from_csv(args.csv)
    if not device_ids:
        print("CSV 未找到 device_id 列或无有效设备ID")
        return 1
    mongo_cfg = {
        "host": args.mongo_host,
        "port": args.mongo_port,
        "username": args.mongo_username,
        "password": args.mongo_password,
        "database": args.mongo_database,
        "collection": args.mongo_collection,
    }
    try:
        client, coll = connect_mongo(mongo_cfg)
    except Exception as e:
        print(f"连接 Mongo 失败: {e}")
        return 2
    output_dir = normalize_windows_path(args.output_dir)
    written_files: List[str] = []
    for did in device_ids:
        rows = fetch_records_for_device(
            coll,
            did,
            max_per_device=args.max_per_device,
            date_from=args.date_from,
            date_to=args.date_to,
        )
        if not rows:
            print(f"设备 {did} 未查询到记录")
            continue
        processed_entries, data_count, collect_count, wear_user_id = decompress_and_build_entries(rows)
        out_path = write_device_json(
            output_dir,
            did,
            wear_user_id,
            processed_entries,
            data_count,
            collect_count,
        )
        written_files.append(out_path)
    print("生成完成：")
    for p in written_files:
        print(f"- {p}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
