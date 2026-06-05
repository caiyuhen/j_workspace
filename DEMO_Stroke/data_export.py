#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_export.py

功能：
- 连接MongoDB并按时间窗口（collectTime在UTC）查询记录；
- 提取 deviceId、collectTime、createTime、collectData；
- 使用 decompressed_comp_ppg_data.py 对 collectData 进行解压；
- 构造与 output 中 JSON 文件结构一致的结果；
- 将结果按设备分文件导出到 output121 目录。

新增：
- 支持在指定时间区间内按小时分段提取（--by-hour）。
- 支持在指定时间区间内按指定分钟分段提取（--segment-minutes 例如 30）。
  分段模式下为每个时间段分别查询与写出；文件名包含时间标签（到分钟）。

用法示例：
python data_export.py --start "2025-11-08 00:00:00" --end "2025-11-08 23:59:59"

说明：
- 输入时间默认视为北京时间（Asia/Shanghai），脚本会转换为UTC后查询 collectTime。
- 若希望输入时间即为UTC，可使用 --tz utc。
"""

import os
import sys
import json
import logging
import shutil
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

import pytz
from pymongo import MongoClient
try:
    import orjson  # 可选更快的JSON写入
    _ORJSON_AVAILABLE = True
except Exception:
    _ORJSON_AVAILABLE = False

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
OUTPUT_DIR = os.path.join(BASE_DIR, 'output121')
LOG_FILE = os.path.join(BASE_DIR, 'script.log')

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.utc


# ===================== 工具函数 =====================
def setup_logging():
    """设置日志：磁盘空间不足时降级为仅控制台，并抑制日志异常堆栈。"""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    except Exception:
        pass
    handlers = [logging.StreamHandler(sys.stdout)]
    try:
        log_dir = os.path.dirname(LOG_FILE) or BASE_DIR
        free_bytes = shutil.disk_usage(log_dir).free
        if free_bytes > 1 * 1024 * 1024:
            handlers.insert(0, logging.FileHandler(LOG_FILE, encoding='utf-8'))
    except Exception:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=handlers
    )
    logging.raiseExceptions = False


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"创建输出目录: {OUTPUT_DIR}")


def beijing_to_utc(dt: datetime) -> datetime:
    """将北京时间转换为UTC时间；接受naive或tz-aware datetime或字符串。"""
    if isinstance(dt, str):
        # 常用格式尝试解析
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
    """将UTC时间转换为北京时间字符串；支持naive或tz-aware或字符串。"""
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
    """格式化UTC时间为字符串，保留微秒（若存在），接受字符串或datetime。"""
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


def _serialize_json_bytes(data: Dict[str, Any]) -> bytes:
    """将数据序列化为UTF-8字节，统一写入路径并便于空间预估。"""
    if _ORJSON_AVAILABLE:
        try:
            return orjson.dumps(data)
        except Exception:
            pass
    s = json.dumps(data, ensure_ascii=False, default=_json_default)
    return s.encode('utf-8')


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

    def fetch_by_collect_time_range(self, start_utc: datetime, end_utc: datetime, *, inclusive_end: bool = True) -> List[Dict[str, Any]]:
        """按 collectTime UTC范围查询，返回必要字段。
        inclusive_end=True 使用 $lte；否则使用 $lt 以避免边界重复。
        """
        rng = {'$gte': start_utc}
        if inclusive_end:
            rng['$lte'] = end_utc
        else:
            rng['$lt'] = end_utc
        query = {'collectTime': rng}
        projection = {
            'deviceId': 1,
            'collectTime': 1,
            'createTime': 1,
            'collectData': 1,
            '_id': 0,
        }
        try:
            cursor = self.col.find(query, projection).sort('collectTime', 1).batch_size(500)
            results = list(cursor)
            logging.info(f"窗口内记录数: {len(results)}")
            return results
        except Exception as e:
            logging.error(f"Mongo 查询失败: {e}")
            return []

    def distinct_device_ids_by_time(self, start_utc: datetime, end_utc: datetime, *, inclusive_end: bool = True) -> List[str]:
        """获取时间窗口内的唯一 deviceId 列表。"""
        rng = {'$gte': start_utc}
        if inclusive_end:
            rng['$lte'] = end_utc
        else:
            rng['$lt'] = end_utc
        query = {'collectTime': rng}
        try:
            device_ids = self.col.distinct('deviceId', query)
            device_ids = [str(d) for d in device_ids if d]
            logging.info(f"窗口内涉及设备数: {len(device_ids)}")
            return device_ids
        except Exception as e:
            logging.error(f"Mongo distinct deviceId 失败: {e}")
            return []

    def fetch_device_docs(self, device_id: str, start_utc: datetime, end_utc: datetime, limit: Optional[int] = None, *, inclusive_end: bool = True) -> List[Dict[str, Any]]:
        """按设备与时间窗口提取文档，支持限制返回条数。"""
        rng = {'$gte': start_utc}
        if inclusive_end:
            rng['$lte'] = end_utc
        else:
            rng['$lt'] = end_utc
        query = {
            'deviceId': device_id,
            'collectTime': rng,
        }
        projection = {
            'deviceId': 1,
            'collectTime': 1,
            'createTime': 1,
            'collectData': 1,
            '_id': 0,
        }
        try:
            cursor = self.col.find(query, projection).sort('collectTime', 1).batch_size(500)
            if limit and limit > 0:
                cursor = cursor.limit(limit)
            docs = list(cursor)
            return docs
        except Exception as e:
            logging.warning(f"设备{device_id} 查询失败: {e}")
            return []


# ===================== 数据处理 =====================
def group_by_device(docs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for d in docs:
        device_id = str(d.get('deviceId') or '')
        if not device_id:
            # 跳过无设备ID的数据
            continue
        grouped.setdefault(device_id, []).append(d)
    return grouped


def build_processed_json(device_id: str, raw_items: List[Dict[str, Any]], *, skip_decompress: bool = False, no_beijing: bool = False, window_start: Optional[datetime] = None, window_end: Optional[datetime] = None) -> Dict[str, Any]:
    """构造输出JSON并进行解压。
    可选：skip_decompress 跳过解压；no_beijing 跳过北京时间字符串转换（填空字符串）。
    """
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
    if skip_decompress:
        decompressed = [None] * len(extract_list)
    else:
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
            'collectTime_beijing': ("" if no_beijing else utc_to_beijing_str(orig.get('collectTime'))),
            'createTime_beijing': ("" if no_beijing else utc_to_beijing_str(orig.get('createTime'))),
            'originalDataSize': len(orig.get('collectData') or b'') if isinstance(orig.get('collectData'), (bytes, bytearray)) else (len(orig.get('collectData') or []) if hasattr(orig.get('collectData'), '__len__') else 0),
            'decompressedData': dec,
            'decompressedDataSize': len(dec or []) if hasattr(dec, '__len__') else 0,
            'success': (False if skip_decompress else (dec is not None)),
        })

    payload = {
        'deviceId': device_id,
        'dataCount': len(raw_items),
        'collectDataCount': len(extract_list),
        'processedData': processed_data,
        'processTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'success': True,
    }
    # 可选添加窗口信息，便于追踪小时分段
    if window_start is not None:
        payload['windowStartUtc'] = format_utc_time(window_start)
    if window_end is not None:
        payload['windowEndUtc'] = format_utc_time(window_end)
    return payload


def write_json(device_id: str, data: Dict[str, Any], *, time_tag: Optional[str] = None) -> str:
    ts = time_tag or datetime.now().strftime('%Y%m%d_%H%M%S')
    fn = f"{device_id}_{ts}.json"
    fp = os.path.join(OUTPUT_DIR, fn)
    try:
        encoded = _serialize_json_bytes(data)
        need_bytes = len(encoded) + 4096
        try:
            free_bytes = shutil.disk_usage(OUTPUT_DIR).free
        except Exception:
            free_bytes = None
        if free_bytes is not None and free_bytes < need_bytes:
            logging.error(f"磁盘空间不足，无法写出 {fp}。剩余 {free_bytes}B，预计需要 {need_bytes}B。请更换 --output-dir 或释放空间。")
            return fp
        with open(fp, 'wb') as f:
            f.write(encoded)
        logging.info(f"写出文件: {fp}")
        return fp
    except Exception as e:
        logging.error(f"写出JSON失败({fp}): {e}")
        return fp


# ===================== CLI 与主流程 =====================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='导出指定时间窗口的设备压缩数据并解压生成JSON')
    parser.add_argument('--start', required=True, help='开始时间，格式如 2025-11-08 或 2025-11-08 12:00:00')
    parser.add_argument('--end', required=True, help='结束时间，格式如 2025-11-08 或 2025-11-08 23:59:59')
    parser.add_argument('--tz', choices=['beijing', 'utc'], default='beijing', help='输入时间的时区（默认北京）')
    parser.add_argument('--by-hour', action='store_true', help='在时间区间内按小时分段提取（每段60分钟）')
    parser.add_argument('--segment-minutes', type=int, default=None, help='在时间区间内按指定分钟分段提取，如 30')
    parser.add_argument('--one-file-per-device', action='store_true', help='每设备仅生成一个JSON文件（分段模式下合并写出）')
    parser.add_argument('--output-dir', default=None, help='输出目录（默认使用脚本内配置的output121）')
    parser.add_argument('--min-free-mb', type=int, default=50, help='写出前最低可用空间阈值（MB），不足则停止写出')
    # 速度优化相关开关
    parser.add_argument('--skip-decompress', action='store_true', help='跳过解压，显著提升速度与减少内存')
    parser.add_argument('--no-beijing', action='store_true', help='不计算北京时间字符串字段，减少CPU开销')
    parser.add_argument('--max-devices', type=int, default=None, help='最多处理的设备数量（默认全部）')
    parser.add_argument('--limit-per-device', type=int, default=None, help='每设备最多处理的记录数（按 collectTime 排序）')
    parser.add_argument('--workers', type=int, default=1, help='并行设备处理的工作线程数（建议<=CPU核心数）')
    return parser.parse_args()


def parse_input_time_to_utc(s: str, tz_mode: str) -> datetime:
    # 解析字符串到datetime
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
        # 输入即为UTC
        return dt.replace(tzinfo=UTC_TZ)
    # 默认视为北京时间
    return beijing_to_utc(dt)


def main():
    args = parse_args()
    global OUTPUT_DIR
    if args.output_dir:
        try:
            OUTPUT_DIR = os.path.abspath(args.output_dir)
        except Exception:
            pass
    setup_logging()
    ensure_output_dir()
    # 启动阶段磁盘空间预检
    try:
        free_bytes = shutil.disk_usage(OUTPUT_DIR).free
        min_bytes = max(0, int(args.min_free_mb)) * 1024 * 1024
        if free_bytes < min_bytes:
            logging.error(f"磁盘可用空间不足：{free_bytes}B < {min_bytes}B。请释放空间或指定 --output-dir 改用有空间的目录。程序停止以避免错误。")
            return
    except Exception as e:
        logging.warning(f"磁盘空间预检失败：{e}")
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
    seg_minutes = args.segment_minutes if args.segment_minutes else (60 if args.by_hour else None)
    if seg_minutes:
        logging.info(f"启用分段模式：每段 {seg_minutes} 分钟")
        if args.one_file_per_device:
            logging.info("分段提取但每设备合并为单文件")

    mongo = MongoExtractor(MONGO_CONFIG)
    if not mongo.connect():
        logging.error("MongoDB连接失败，程序退出")
        sys.exit(2)

    try:
        # 若指定设备限流或并行，则采用设备粒度查询与处理
        device_mode = (args.limit_per_device is not None) or (args.max_devices is not None) or (args.workers and args.workers > 1)
        written_files: List[str] = []

        # 如果启用分段模式，则将大窗口拆分为多个分钟段
        if seg_minutes and args.one_file_per_device:
            # 分段聚合：按段查询，累计到每设备聚合，最终一次性写出
            agg_items_by_device: defaultdict[str, List[Dict[str, Any]]] = defaultdict(list)
            added_counts: defaultdict[str, int] = defaultdict(int)

            if device_mode:
                # 先确定窗口内设备列表，便于限流与并行后续处理
                device_ids = mongo.distinct_device_ids_by_time(start_utc, end_utc, inclusive_end=True)
                if not device_ids:
                    logging.warning("在指定时间窗口内未检索到任何设备")
                    return
                if args.max_devices:
                    device_ids = device_ids[:max(0, args.max_devices)]

                cur = start_utc
                seg_idx = 0
                while cur < end_utc:
                    seg_start = cur
                    seg_end_candidate = cur + timedelta(minutes=seg_minutes)
                    seg_end = seg_end_candidate if seg_end_candidate < end_utc else end_utc
                    inclusive_end = (seg_end == end_utc)
                    seg_idx += 1
                    logging.info(f"分段[{seg_idx}] (UTC): {format_utc_time(seg_start)} ~ {format_utc_time(seg_end)} | inclusive_end={inclusive_end}")

                    for did in device_ids:
                        # 处理每设备限流：计算剩余可添加条数
                        remaining: Optional[int] = None
                        if args.limit_per_device is not None:
                            remaining = max(0, args.limit_per_device - added_counts[did])
                            if remaining == 0:
                                continue
                        items = mongo.fetch_device_docs(did, seg_start, seg_end, limit=(remaining if (remaining and remaining > 0) else None), inclusive_end=inclusive_end)
                        if not items:
                            continue
                        agg_items_by_device[did].extend(items)
                        added_counts[did] += len(items)

                    cur = seg_end
            else:
                # 非设备模式：按段查询并分组后累计到聚合
                discovered: List[str] = []
                cur = start_utc
                seg_idx = 0
                while cur < end_utc:
                    seg_start = cur
                    seg_end_candidate = cur + timedelta(minutes=seg_minutes)
                    seg_end = seg_end_candidate if seg_end_candidate < end_utc else end_utc
                    inclusive_end = (seg_end == end_utc)
                    seg_idx += 1
                    logging.info(f"分段[{seg_idx}] (UTC): {format_utc_time(seg_start)} ~ {format_utc_time(seg_end)} | inclusive_end={inclusive_end}")

                    docs = mongo.fetch_by_collect_time_range(seg_start, seg_end, inclusive_end=inclusive_end)
                    if not docs:
                        cur = seg_end
                        continue
                    groups = group_by_device(docs)
                    for did, items in groups.items():
                        # 控制最多设备数量
                        if args.max_devices is not None:
                            if did not in discovered and len(discovered) >= max(0, args.max_devices):
                                continue
                        if did not in discovered:
                            discovered.append(did)
                        # 每设备限流：仅累计到剩余上限
                        if args.limit_per_device is not None:
                            remaining = max(0, args.limit_per_device - added_counts[did])
                            if remaining == 0:
                                continue
                            if len(items) > remaining:
                                items = items[:remaining]
                        agg_items_by_device[did].extend(items)
                        added_counts[did] += len(items)
                    cur = seg_end

            # 最终一次性为每设备写出单文件
            def build_and_write(did: str) -> Optional[str]:
                items = agg_items_by_device.get(did, [])
                if not items:
                    return None
                payload = build_processed_json(did, items, skip_decompress=args.skip_decompress, no_beijing=args.no_beijing, window_start=start_utc, window_end=end_utc)
                return write_json(did, payload)

            device_list = list(agg_items_by_device.keys())
            if args.workers and args.workers > 1:
                with ThreadPoolExecutor(max_workers=args.workers) as ex:
                    futs = {ex.submit(build_and_write, did): did for did in device_list}
                    for fut in as_completed(futs):
                        try:
                            fp = fut.result()
                            if fp:
                                written_files.append(fp)
                        except Exception as e:
                            logging.warning(f"设备 {futs[fut]} 合并处理失败: {e}")
            else:
                for did in device_list:
                    fp = build_and_write(did)
                    if fp:
                        written_files.append(fp)
        elif seg_minutes:
            cur = start_utc
            seg_idx = 0
            while cur < end_utc:
                seg_start = cur
                seg_end_candidate = cur + timedelta(minutes=seg_minutes)
                seg_end = seg_end_candidate if seg_end_candidate < end_utc else end_utc
                inclusive_end = (seg_end == end_utc)
                seg_idx += 1
                logging.info(f"分段[{seg_idx}] (UTC): {format_utc_time(seg_start)} ~ {format_utc_time(seg_end)} | inclusive_end={inclusive_end}")

                # 时间标签到分钟，以UTC标注
                time_tag = seg_start.astimezone(UTC_TZ).strftime('%Y%m%d_%H%M')

                if device_mode:
                    device_ids = mongo.distinct_device_ids_by_time(seg_start, seg_end, inclusive_end=inclusive_end)
                    if not device_ids:
                        logging.info("此时间段无设备数据")
                        cur = seg_end
                        continue
                    if args.max_devices:
                        device_ids = device_ids[:max(0, args.max_devices)]

                    def process_one_hour(did: str) -> Optional[str]:
                        items = mongo.fetch_device_docs(did, seg_start, seg_end, limit=args.limit_per_device, inclusive_end=inclusive_end)
                        if not items:
                            return None
                        payload = build_processed_json(did, items, skip_decompress=args.skip_decompress, no_beijing=args.no_beijing, window_start=seg_start, window_end=seg_end)
                        return write_json(did, payload, time_tag=time_tag)

                    if args.workers and args.workers > 1:
                        with ThreadPoolExecutor(max_workers=args.workers) as ex:
                            futs = {ex.submit(process_one_hour, did): did for did in device_ids}
                            for fut in as_completed(futs):
                                try:
                                    fp = fut.result()
                                    if fp:
                                        written_files.append(fp)
                                except Exception as e:
                                    logging.warning(f"设备 {futs[fut]} 小时段处理失败: {e}")
                    else:
                        for did in device_ids:
                            fp = process_one_hour(did)
                            if fp:
                                written_files.append(fp)
                else:
                    # 非设备模式：每段拉取、分组并写出
                    docs = mongo.fetch_by_collect_time_range(seg_start, seg_end, inclusive_end=inclusive_end)
                    if not docs:
                        logging.info("此时间段无记录")
                        cur = seg_end
                        continue
                    groups = group_by_device(docs)
                    logging.info(f"此时间段涉及设备数: {len(groups)}")
                    for device_id, items in groups.items():
                        payload = build_processed_json(device_id, items, skip_decompress=args.skip_decompress, no_beijing=args.no_beijing, window_start=seg_start, window_end=seg_end)
                        fp = write_json(device_id, payload, time_tag=time_tag)
                        written_files.append(fp)

                cur = seg_end
        else:
            # 原有路径：整个窗口一次性处理
            if device_mode:
                device_ids = mongo.distinct_device_ids_by_time(start_utc, end_utc, inclusive_end=True)
                if not device_ids:
                    logging.warning("在指定时间窗口内未检索到任何设备")
                    return
                if args.max_devices:
                    device_ids = device_ids[:max(0, args.max_devices)]

                def process_one(did: str) -> Optional[str]:
                    items = mongo.fetch_device_docs(did, start_utc, end_utc, limit=args.limit_per_device, inclusive_end=True)
                    if not items:
                        return None
                    payload = build_processed_json(did, items, skip_decompress=args.skip_decompress, no_beijing=args.no_beijing, window_start=start_utc, window_end=end_utc)
                    return write_json(did, payload)

                if args.workers and args.workers > 1:
                    with ThreadPoolExecutor(max_workers=args.workers) as ex:
                        futs = {ex.submit(process_one, did): did for did in device_ids}
                        for fut in as_completed(futs):
                            try:
                                fp = fut.result()
                                if fp:
                                    written_files.append(fp)
                            except Exception as e:
                                logging.warning(f"设备 {futs[fut]} 处理失败: {e}")
                else:
                    for did in device_ids:
                        fp = process_one(did)
                        if fp:
                            written_files.append(fp)
            else:
                # 兼容旧路径：一次性拉取并分组
                docs = mongo.fetch_by_collect_time_range(start_utc, end_utc, inclusive_end=True)
                if not docs:
                    logging.warning("在指定时间窗口内未检索到任何记录")
                    return
                groups = group_by_device(docs)
                logging.info(f"涉及设备数: {len(groups)}")
                for device_id, items in groups.items():
                    payload = build_processed_json(device_id, items, skip_decompress=args.skip_decompress, no_beijing=args.no_beijing, window_start=start_utc, window_end=end_utc)
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