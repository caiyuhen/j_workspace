#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reseach_data.py

功能：
- 连接MySQL，从 andun_health.h_health_analysis 按时间范围筛选记录；解析 models 中“心”“脊柱”状态；
- 按配额分别提取“心”与“脊柱”状态为1/2/3的 T_WEAR_USER_ID；
- 通过 andun_watch.user_wear_active_data 获取 device_id；
- 依据 device_id 与 create_time（转UTC）从 MongoDB andun_1.device_collect_compress_data 提取数据；
- 使用 decompressed_comp_ppg_data.py 的解压函数解压 collectData；
- 生成与 output 目录内JSON结构一致的文件，附加 wear_user_id 字段，导出至 output1；
- 记录执行进度与错误日志至 script.log。

效率：
- 连接与查询均复用已验证逻辑；
- Mongo查询按 create_time ±12小时窗口限定；
- 并发处理所选案例以提升总体速度。
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import argparse
import pymysql
from pymongo import MongoClient
import pytz

# 依赖模块：解压函数
from decompressed_comp_ppg_data import decompressed_and_upsampled_ppg_data

# ===================== 配置区 =====================
# MySQL配置（用户提供）
MYSQL_HOST = "rr-2ze57t6e5586l181hyo.mysql.rds.aliyuncs.com"
MYSQL_PORT = 3306
MYSQL_USER = "ppg_reader"
MYSQL_PASSWORD = "Bm*PiyeQjD6cGii"

# MongoDB配置（用户提供）
MONGO_CONFIG = {
    'host': 'mongoreplica29ed1d62f12a1.mongodb.cn-beijing.volces.com',
    'port': 3717,
    'username': 'apps-wr',
    'password': 'eEcc7U!nNM3ivzC^f',
    'database': 'andun_1',
    'collection': 'device_collect_compress_data'
}

# 输出与日志
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output1')
LOG_FILE = os.path.join(BASE_DIR, 'script.log')

# 并发参数（可按机器性能调整）
MAX_WORKERS = 6

# 时间转换
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.utc


def setup_logging():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"创建输出目录: {OUTPUT_DIR}")


def beijing_to_utc(dt: datetime) -> datetime:
    """将北京时间转换为UTC时间。
    接受naive或已带tz的datetime；naive视为北京时间。
    """
    # 允许字符串输入，尽量解析为datetime
    if isinstance(dt, str):
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except Exception:
                pass
        if isinstance(dt, str):
            raise ValueError(f"无法解析时间字符串: {dt}")

    # 如果是naive，按北京时间本地化；如果已有tz，则先转换到北京时间
    if dt.tzinfo is None:
        bj_dt = BEIJING_TZ.localize(dt)
    else:
        bj_dt = dt.astimezone(BEIJING_TZ)
    return bj_dt.astimezone(UTC_TZ)


def utc_to_beijing_str(dt: Optional[datetime]) -> str:
    """将UTC时间转换为北京时间字符串。
    支持naive或tz-aware；naive按UTC处理。
    """
    if not dt:
        return ""
    if isinstance(dt, str):
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except Exception:
                pass
        # 若仍为字符串，直接返回原值以避免崩溃
        if isinstance(dt, str):
            return dt
    # 若为naive，当作UTC；否则先归一到UTC
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=UTC_TZ)
    else:
        dt_utc = dt.astimezone(UTC_TZ)
    return dt_utc.astimezone(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')


def format_utc_time(dt: Optional[datetime]) -> str:
    """格式化UTC时间为字符串，保留微秒（若存在）。
    支持naive或tz-aware；naive按UTC处理。
    """
    if not dt:
        return ""
    if isinstance(dt, str):
        # 尝试解析字符串为datetime
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except Exception:
                pass
        if isinstance(dt, str):
            return dt
    # 统一至UTC
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=UTC_TZ)
    else:
        dt_utc = dt.astimezone(UTC_TZ)
    if dt_utc.microsecond:
        return dt_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    return dt_utc.strftime('%Y-%m-%d %H:%M:%S')


def compute_mysql_time_window() -> Tuple[datetime, datetime]:
    """计算 create_time 的筛选窗口：
    [当前北京时间-2天 的 12:00:00, 当前北京时间-1天 的 12:00:00]
    """
    now_bj = datetime.now(BEIJING_TZ)
    start_bj = (now_bj - timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
    end_bj = (now_bj - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    # MySQL使用本地时间字符串，无需UTC转换
    # 返回naive字符串或timezone-aware均可，pymysql可接受str
    return start_bj.replace(tzinfo=None), end_bj.replace(tzinfo=None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='按时间窗口从MySQL与Mongo提取并解压导出数据')
    parser.add_argument('--start', help='开始时间，格式如 2025-11-08 或 2025-11-08 12:00:00')
    parser.add_argument('--end', help='结束时间，格式如 2025-11-08 或 2025-11-08 23:59:59')
    parser.add_argument('--tz', choices=['beijing', 'utc'], default='beijing', help='输入时间的时区（默认北京）')
    parser.add_argument('--limit', type=int, help='限制最多读取的健康分析记录数，用于快速验证')
    parser.add_argument('--window', type=int, default=12, help='Mongo 查询窗口（小时），默认为±12小时')
    return parser.parse_args()


def parse_time_to_beijing_naive(s: str, tz_mode: str) -> datetime:
    """将输入时间解析为北京时间的 naive datetime（用于MySQL查询）。"""
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
        dt = dt.replace(tzinfo=UTC_TZ).astimezone(BEIJING_TZ)
    else:
        dt = BEIJING_TZ.localize(dt)
    return dt.replace(tzinfo=None)


def get_mysql_conn(db_name: str) -> Optional[pymysql.connections.Connection]:
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            read_timeout=20,
            write_timeout=20,
        )
        return conn
    except Exception as e:
        logging.error(f"连接数据库 {db_name} 失败: {e}")
        return None


def parse_models_status(models_json_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """解析 models 的“心”“脊柱/脊椎” status 值。
    返回：(heart_status, spine_status)
    """
    heart_status: Optional[int] = None
    spine_status: Optional[int] = None
    if not models_json_str:
        return heart_status, spine_status
    try:
        data = json.loads(models_json_str)
        # 统一成列表
        organs: List[Dict[str, Any]] = []
        if isinstance(data, list):
            organs = data
        elif isinstance(data, dict):
            if isinstance(data.get('organs'), list):
                organs = data['organs']
            else:
                organs = [data]
        for organ in organs:
            if not isinstance(organ, dict):
                continue
            name = organ.get('name')
            status = organ.get('status')
            if name == '心':
                try:
                    heart_status = int(status)
                except Exception:
                    heart_status = None
            elif name in ('脊柱', '脊椎'):
                try:
                    spine_status = int(status)
                except Exception:
                    spine_status = None
    except Exception:
        pass
    return heart_status, spine_status


def fetch_health_records(conn_health: pymysql.connections.Connection,
                         start_dt: datetime, end_dt: datetime,
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """按 create_time 窗口获取 h_health_analysis 记录。"""
    base_sql = (
        "SELECT T_WEAR_USER_ID, source_date, create_time, models FROM h_health_analysis "
        "WHERE create_time >= %s AND create_time <= %s"
    )
    # 为快速验证可选择限制数量
    sql = base_sql + (" ORDER BY create_time DESC LIMIT %s" if limit and limit > 0 else "")
    try:
        with conn_health.cursor() as cur:
            params = [start_dt.strftime('%Y-%m-%d %H:%M:%S'), end_dt.strftime('%Y-%m-%d %H:%M:%S')]
            if limit and limit > 0:
                params.append(int(limit))
            cur.execute(sql, tuple(params))
            rows = cur.fetchall() or []
            logging.info(f"andun_health.h_health_analysis 记录数: {len(rows)}")
            return rows
    except Exception as e:
        logging.error(f"查询 h_health_analysis 失败: {e}")
        return []


def select_quota(records: List[Dict[str, Any]], key: str, target_status: int, quota: int) -> List[Dict[str, Any]]:
    """按指定状态和配额选择记录，key ∈ {heart_status, spine_status}。"""
    filtered = [r for r in records if r.get(key) == target_status]
    # 统一 create_time 为字符串/datetime，做排序保证稳定输出
    def ct_sort_val(r):
        ct = r.get('create_time')
        if isinstance(ct, datetime):
            return ct
        try:
            return datetime.strptime(str(ct), '%Y-%m-%d %H:%M:%S')
        except Exception:
            return datetime.min
    filtered.sort(key=ct_sort_val)
    selected = filtered[:quota]
    logging.info(f"选择 {key}={target_status} 数量: {len(selected)}/{quota}")
    return selected


def fetch_device_id(conn_watch: pymysql.connections.Connection, wear_user_id: str) -> Optional[str]:
    """在 andun_watch.user_wear_active_data 查询最近的 device_id。"""
    sql_candidates = [
        # 去除可能不存在的列 update_time
        "SELECT device_id,count(*) FROM user_wear_active_data WHERE wear_user_id=%s",
      
    ]
    for sql in sql_candidates:
        try:
            with conn_watch.cursor() as cur:
                cur.execute(sql, (wear_user_id,))
                row = cur.fetchone()
                if row and row.get('device_id'):
                    return str(row['device_id'])
        except Exception as e:
            logging.warning(f"查询 device_id 失败(wear_user_id={wear_user_id}): {e}")
            continue
    return None


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

    def fetch_by_device_and_time(self, device_id: str, center_bj_time: datetime,
                                 hours_window: int = 12) -> List[Dict[str, Any]]:
        """按 deviceId 与 createTime（UTC）窗口查询记录。"""
        start_utc = beijing_to_utc(center_bj_time - timedelta(hours=hours_window))
        end_utc = beijing_to_utc(center_bj_time + timedelta(hours=hours_window))
        query = {
            'deviceId': device_id,
            'createTime': {
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
            logging.info(f"Mongo 设备{device_id} 在窗口内记录数: {len(results)}")
            return results
        except Exception as e:
            logging.error(f"Mongo 查询失败(device_id={device_id}): {e}")
            return []


def build_processed_json(device_id: str, wear_user_id: str, raw_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """构造输出JSON结构并进行解压。"""
    # 仅对包含 collectData 的项进行解压
    extract_list: List[Dict[str, Any]] = []
    for it in raw_items:
        if it.get('collectData'):
            extract_list.append({
                'collectTime': it.get('collectTime'),
                'createTime': it.get('createTime'),
                'collectData': it.get('collectData'),
                'deviceId': it.get('deviceId'),
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
        'wear_user_id': wear_user_id,
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
    # 安全的默认序列化，处理 datetime、bytes、numpy 数值等
    def _json_default(obj):
        try:
            # datetime 转统一UTC字符串
            if isinstance(obj, datetime):
                return format_utc_time(obj)
            # bytes/bytearray 转为十六进制字符串，避免膨胀
            if isinstance(obj, (bytes, bytearray)):
                return obj.hex()
            # 其它对象尝试使用 isoformat（如有）
            if hasattr(obj, 'isoformat') and callable(getattr(obj, 'isoformat')):
                return obj.isoformat()
            # numpy 类型处理为原生Python类型
            import numpy as np  # 局部导入避免顶层依赖
            if isinstance(obj, (np.integer, )):
                return int(obj)
            if isinstance(obj, (np.floating, )):
                return float(obj)
            if isinstance(obj, (np.ndarray, )):
                return obj.tolist()
        except Exception:
            pass
        # 最后兜底为字符串
        return str(obj)
    try:
        # 为兼容性使用标准json写入（orjson可选）
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=_json_default)
        logging.info(f"写出文件: {fp}")
        return fp
    except Exception as e:
        logging.error(f"写出JSON失败({fp}): {e}")
        return fp


def main():
    setup_logging()
    ensure_output_dir()
    args = parse_args()

    # 建立MySQL连接
    conn_health = get_mysql_conn('andun_health')
    conn_watch = get_mysql_conn('andun_watch')
    if not conn_health or not conn_watch:
        logging.error('数据库连接失败，程序退出')
        return

    # 计算时间窗口并查询记录
    if args.start and args.end:
        try:
            start_dt = parse_time_to_beijing_naive(args.start, args.tz)
            end_dt = parse_time_to_beijing_naive(args.end, args.tz)
        except Exception as e:
            logging.error(f"解析时间参数失败: {e}")
            return
        if end_dt < start_dt:
            logging.error("结束时间早于开始时间")
            return
    else:
        start_dt, end_dt = compute_mysql_time_window()
    logging.info(f"筛选窗口: {start_dt} ~ {end_dt}")
    records = fetch_health_records(conn_health, start_dt, end_dt, limit=args.limit)

    # 解析 models 状态并附加到记录
    enriched: List[Dict[str, Any]] = []
    for r in records:
        heart_status, spine_status = parse_models_status(r.get('models'))
        enriched.append({
            **r,
            'heart_status': heart_status,
            'spine_status': spine_status,
        })

    # 按配额选择
    heart_s1 = select_quota(enriched, 'heart_status', 1, 150)
    heart_s2 = select_quota(enriched, 'heart_status', 2, 80)
    heart_s3 = select_quota(enriched, 'heart_status', 3, 60)

    spine_s1 = select_quota(enriched, 'spine_status', 1, 150)
    spine_s2 = select_quota(enriched, 'spine_status', 2, 80)
    spine_s3 = select_quota(enriched, 'spine_status', 3, 60)

    # 合并所选案例（心 + 脊柱），去重按 wear_user_id + create_time + tag
    selected_cases: List[Tuple[str, datetime]] = []  # (wear_user_id, create_time)
    def append_cases(items: List[Dict[str, Any]]):
        for it in items:
            wuid = str(it.get('T_WEAR_USER_ID'))
            ct = it.get('create_time')
            if not isinstance(ct, datetime):
                try:
                    ct = datetime.strptime(str(ct), '%Y-%m-%d %H:%M:%S')
                except Exception:
                    ct = start_dt
            selected_cases.append((wuid, ct))

    append_cases(heart_s1); append_cases(heart_s2); append_cases(heart_s3)
    append_cases(spine_s1); append_cases(spine_s2); append_cases(spine_s3)

    logging.info(f"总选取案例数: {len(selected_cases)}")

    # 连接Mongo
    mongo = MongoExtractor(MONGO_CONFIG)
    if not mongo.connect():
        logging.error('MongoDB连接失败，程序退出')
        try:
            conn_health and conn_health.close()
            conn_watch and conn_watch.close()
        except Exception:
            pass
        return

    # 处理每个案例
    processed_files: List[str] = []
    for wear_user_id, center_ct in selected_cases:
        device_id = fetch_device_id(conn_watch, wear_user_id)
        if not device_id:
            logging.warning(f"未找到 device_id (wear_user_id={wear_user_id})，跳过")
            continue

        raw_items = mongo.fetch_by_device_and_time(device_id, center_ct, hours_window=args.window)
        if not raw_items:
            logging.warning(f"Mongo无数据(device_id={device_id}, ct={center_ct})")
            continue

        payload = build_processed_json(device_id, wear_user_id, raw_items)
        fp = write_json(device_id, payload)
        processed_files.append(fp)

    logging.info(f"处理完成，生成文件数: {len(processed_files)}")

    # 关闭连接
    try:
        mongo.disconnect()
        conn_health and conn_health.close()
        conn_watch and conn_watch.close()
    except Exception:
        pass


if __name__ == '__main__':
    main()