#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_export0909.py

功能：
- 连接 MongoDB 并按时间窗口（collectTime 在 UTC）查询记录；
- 提取 deviceId、collectTime、createTime、collectData；
- 使用 decompressed_comp_ppg_data.py 对 collectData 进行解压；
- 构造与 output 中 JSON 文件结构一致的结果；
- 将结果按设备分文件导出到 output121 目录。

用法示例：
python data_export0909.py --start "2025-11-08 00:00:00" --end "2025-11-08 23:59:59"

说明：
- 输入时间默认视为北京时间（Asia/Shanghai），脚本会转换为 UTC 后查询 collectTime。
- 若希望输入时间即为 UTC，可使用 --tz utc。
"""

import os
import sys
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import argparse

import pytz
from pymongo import MongoClient

# 解压模块
from decompressed_comp_ppg_data import decompressed_and_upsampled_ppg_data

# ===================== 配置区 =====================
MONGO_CONFIG = {
    'host': 'mongoreplica29ed1d62f12a1.mongodb.cn-beijing.volces.com',
    'port': 3717,
    'username': 'apps-wr',
    'password': 'eEcc7U!nNM3ivzC^f',
    'database': 'andun_1',
    'collection': 'device_collect_compress_data'
}

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output1212')
LOG_FILE = os.path.join(BASE_DIR, 'script.log')

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.utc


# ===================== 工具函数 =====================

def setup_logging():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"创建输出目录: {OUTPUT_DIR}")


def beijing_to_utc(dt: datetime) -> datetime:
    """将北京时间转换为 UTC 时间；接受 naive 或 tz-aware datetime 或字符串。"""
    if isinstance(dt, str):
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except Exception:
                pass
        if isinstance(dt, str):
            raise ValueError(f"无法解析时间字符串: {dt}")
    if dt.tzinfo is None:
        bj_dt = BEIJING_TZ.localize(dt)
    else:
        bj_dt = dt.astimezone(BEIJING_TZ)
    return bj_dt.astimezone(UTC_TZ)


def utc_to_beijing_str(dt: Optional[datetime]) -> str:
    """将 UTC 时间转换为北京时间字符串；支持 naive 或 tz-aware 或字符串。"""
    if not dt:
        return ""
    if isinstance(dt, str):
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except Exception:
                pass
        if isinstance(dt, str):
            return dt
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=UTC_TZ)
    else:
        dt_utc = dt.astimezone(UTC_TZ)
    return dt_utc.astimezone(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')


def format_utc_time(dt: Optional[datetime]) -> str:
    """格式化 UTC 时间为字符串，保留微秒（若存在），接受字符串或 datetime。"""
    if not dt:
        return ""
    if isinstance(dt, str):
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except Exception:
                pass
        if isinstance(dt, str):
            return dt
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=UTC_TZ)
    else:
        dt_utc = dt.astimezone(UTC_TZ)
    if dt_utc.microsecond:
        return dt_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    return dt_utc.strftime('%Y-%m-%d %H:%M:%S')


def _json_default(obj):
    """安全的默认序列化器：处理 datetime、bytes、numpy 类型等。"""
    try:
        if isinstance(obj, datetime):
            return format_utc_time(obj)
        if isinstance(obj, (bytes, bytearray)):
            return obj.hex()
        if hasattr(obj, 'isoformat') and callable(getattr(obj, 'isoformat')):
            return obj.isoformat()
        import numpy as np
        if isinstance(obj, (np.integer, )):
            return int(obj)
        if isinstance(obj, (np.floating, )):
            return float(obj)
        if isinstance(obj, (np.ndarray, )):
            return obj.tolist()
    except Exception:
        pass
    return str(obj)


# ===================== Mongo 访问 =====================
class MongoExtractor:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.client: Optional[MongoClient] = None
        self.db = None
        self.col = None

    def connect(self) -> bool:
        try:
            uri = (
                f"mongodb://{self.cfg['username']}:{self.cfg['password']}@"
                f"{self.cfg['host']}:{self.cfg['port']}/{self.cfg['database']}?authSource=admin"
            )
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.server_info()
            self.db = self.client[self.cfg['database']]
            self.col = self.db[self.cfg['collection']]
            logging.info("成功连接到MongoDB")
            return True
        except Exception as e:
            logging.error(f"连接MongoDB失败: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
            logging.info("已断开MongoDB连接")

    def fetch_by_collect_time_range(self, start_utc: datetime, end_utc: datetime) -> List[Dict[str, Any]]:
        """按 collectTime UTC 范围查询，返回必要字段。"""
        query = {
            'collectTime': {
                '$gte': start_utc,
                '$lte': end_utc,
            }
        }
        projection = {
            'deviceId': 1,
            'collectTime': 1,
            'createTime': 1,
            'collectData': 1,
            '_id': 0,
        }
        try:
            cursor = self.col.find(query, projection).sort('collectTime', 1)
            results = list(cursor)
            logging.info(f"窗口内记录数: {len(results)}")
            return results
        except Exception as e:
            logging.error(f"Mongo 查询失败: {e}")
            return []


# ===================== 数据处理 =====================
def group_by_device(docs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for d in docs:
        device_id = str(d.get('deviceId') or '')
        if not device_id:
            continue
        grouped.setdefault(device_id, []).append(d)
    return grouped


def build_processed_json(device_id: str, raw_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """构造输出 JSON 并进行解压。"""
    extract_list: List[Dict[str, Any]] = []
    for it in raw_items:
        if it.get('collectData') is not None:
            extract_list.append({
                'deviceId': it.get('deviceId'),
                'collectTime': it.get('collectTime'),
                'createTime': it.get('createTime'),
                'collectData': it.get('collectData'),
            })

    decompressed = []
    try:
        logging.info(f"开始解压设备{device_id} 的 {len(extract_list)} 条数据")
        decompressed = decompressed_and_upsampled_ppg_data(extract_list)
    except Exception as e:
        logging.error(f"解压失败(device_id={device_id}): {e}")
        decompressed = [None] * len(extract_list)

    processed_data: List[Dict[str, Any]] = []
    for idx, (orig, dec) in enumerate(zip(extract_list, decompressed)):
        processed_data.append({
            'index': idx,
            'collectTime': format_utc_time(orig.get('collectTime')),
            'createTime': format_utc_time(orig.get('createTime')),
            'collectTime_beijing': utc_to_beijing_str(orig.get('collectTime')),
            'createTime_beijing': utc_to_beijing_str(orig.get('createTime')),
            'originalDataSize': len(orig.get('collectData') or b'') if isinstance(orig.get('collectData'), (bytes, bytearray)) else (len(orig.get('collectData') or []) if hasattr(orig.get('collectData'), '__len__') else 0),
            'decompressedData': dec,
            'decompressedDataSize': len(dec or []) if hasattr(dec, '__len__') else 0,
            'success': dec is not None,
        })

    return {
        'deviceId': device_id,
        'dataCount': len(raw_items),
        'collectDataCount': len(extract_list),
        'processedData': processed_data,
        'processTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'success': True,
    }


def write_json(device_id: str, data: Dict[str, Any]) -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fn = f"{device_id}_{ts}.json"
    fp = os.path.join(OUTPUT_DIR, fn)
    try:
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=_json_default)
        logging.info(f"写出文件: {fp}")
        return fp
    except Exception as e:
        logging.error(f"写出 JSON 失败({fp}): {e}")
        return fp


# ===================== CLI 与主流程 =====================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='导出指定时间窗口的设备压缩数据并解压生成 JSON')
    parser.add_argument('--start', required=True, help='开始时间，格式如 2025-11-08 或 2025-11-08 12:00:00')
    parser.add_argument('--end', required=True, help='结束时间，格式如 2025-11-08 或 2025-11-08 23:59:59')
    parser.add_argument('--tz', choices=['beijing', 'utc'], default='beijing', help='输入时间的时区（默认北京）')
    return parser.parse_args()


def parse_input_time_to_utc(s: str, tz_mode: str) -> datetime:
    dt: Optional[datetime] = None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(s, fmt)
            break
        except Exception:
            pass
    if dt is None:
        raise ValueError(f"无法解析时间: {s}")
    if tz_mode == 'utc':
        return dt.replace(tzinfo=UTC_TZ)
    return beijing_to_utc(dt)


def main():
    setup_logging()
    ensure_output_dir()

    args = parse_args()
    try:
        start_utc = parse_input_time_to_utc(args.start, args.tz)
        end_utc = parse_input_time_to_utc(args.end, args.tz)
    except Exception as e:
        logging.error(f"解析时间参数失败: {e}")
        sys.exit(1)

    if end_utc < start_utc:
        logging.error("结束时间早于开始时间")
        sys.exit(1)

    logging.info(f"查询窗口(UTC): {format_utc_time(start_utc)} ~ {format_utc_time(end_utc)}")

    mongo = MongoExtractor(MONGO_CONFIG)
    if not mongo.connect():
        logging.error("MongoDB 连接失败，程序退出")
        sys.exit(2)

    try:
        docs = mongo.fetch_by_collect_time_range(start_utc, end_utc)
        if not docs:
            logging.warning("在指定时间窗口内未检索到任何记录")
            return

        groups = group_by_device(docs)
        logging.info(f"涉及设备数: {len(groups)}")

        written_files: List[str] = []
        for device_id, items in groups.items():
            payload = build_processed_json(device_id, items)
            fp = write_json(device_id, payload)
            written_files.append(fp)

        logging.info(f"处理完成，生成文件数: {len(written_files)}")
    finally:
        try:
            mongo.disconnect()
        except Exception:
            pass


if __name__ == '__main__':
    main()