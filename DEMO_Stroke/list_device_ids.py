#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import List

import pymysql


# 数据库配置（按要求）
MYSQL_HOST = "rr-2ze57t6e5586l181hyo.mysql.rds.aliyuncs.com"
MYSQL_PORT = 3306
MYSQL_USER = "ppg_reader"
MYSQL_PASSWORD = "Bm*PiyeQjD6cGii"
# 连接到任一库即可，查询使用完全限定名
MYSQL_DB = "andun_health"


def _connect() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "查询 andun_watch.user_wear_active_data 与 andun_health.h_health_analysis 的联表，"
            "按 source_date 过滤并导出设备ID为 JSON"
        )
    )
    p.add_argument(
        "--source-date",
        help="查询的 source_date（例如 2025-11-06）",
    )
    p.add_argument(
        "--output",
        default="list_device_id_output.json",
        help="输出 JSON 文件路径（默认 list_device_id_output.json）",
    )
    return p.parse_args()


def _query_device_ids_by_source_date(conn: pymysql.connections.Connection, source_date: str) -> List[str]:
    sql = (
        "SELECT DISTINCT uwad.device_id "
        "FROM andun_watch.user_wear_active_data AS uwad "
        "INNER JOIN andun_health.h_health_analysis AS hha "
        "ON uwad.wear_user_id = hha.T_WEAR_USER_ID "
        "WHERE hha.source_date = %s "
        "ORDER BY uwad.device_id"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (source_date,))
        rows = cur.fetchall() or []
    device_ids: List[str] = []
    for r in rows:
        did = r.get("device_id")
        if did is None:
            continue
        device_ids.append(str(did))
    return device_ids


def main():
    args = _parse_args()
    source_date = args.source_date
    if not source_date:
        source_date = input("请输入 source_date（如 2025-11-06）：").strip()
        if not source_date:
            print("未提供 source_date，已退出。")
            sys.exit(1)

    try:
        conn = _connect()
    except Exception as e:
        print(f"数据库连接失败：{e}")
        sys.exit(2)

    try:
        device_ids = _query_device_ids_by_source_date(conn, source_date)
    except Exception as e:
        print(f"查询失败：{e}")
        conn.close()
        sys.exit(3)

    conn.close()

    out_path = os.path.abspath(args.output)
    payload = {
        "count": len(device_ids),
        "device_ids": device_ids,
    }
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"已写出设备ID JSON：{out_path}（count={payload['count']}）")
    except Exception as e:
        print(f"写出 JSON 失败：{e}")


if __name__ == "__main__":
    main()