#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import pymysql


# 数据库配置（按用户要求）
MYSQL_HOST = "rr-2ze57t6e5586l181hyo.mysql.rds.aliyuncs.com"
MYSQL_PORT = 3306
MYSQL_USER = "ppg_reader"
MYSQL_PASSWORD = "Bm*PiyeQjD6cGii"
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
            "按 create_time 精确查询 andun_health.h_health_analysis，提取 wear_user_id、"
            "心/脊柱 status，并统计 status 为 2/3 的记录数量"
        )
    )
    p.add_argument(
        "--create-time",
        required=False,
        help="查询的 create_time（例如 2025-11-07 12:40:01）",
    )
    p.add_argument(
        "--output-csv",
        default="list_file_output.csv",
        help="输出 CSV 文件路径（包含提取到的 wear_user_id 与心/脊柱 status）",
    )
    return p.parse_args()


def _json_loads_relaxed(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except Exception:
        pass
    # 尝试将单引号替换为双引号的简单修复（避免破坏数字/结构）
    try:
        fixed = re.sub(r"'", '"', text)
        return json.loads(fixed)
    except Exception:
        return None


def _extract_statuses_from_models(models_text: str) -> Tuple[Optional[int], Optional[int]]:
    heart_status: Optional[int] = None
    spine_status: Optional[int] = None

    obj = _json_loads_relaxed(models_text)
    if obj is not None:
        candidates: List[Dict[str, Any]] = []
        if isinstance(obj, list):
            candidates = obj  # 期望为列表，每项含 name/status
        elif isinstance(obj, dict):
            if "models" in obj and isinstance(obj["models"], list):
                candidates = obj["models"]
            else:
                # 字典直接包含条目
                candidates = [obj]

        for item in candidates:
            try:
                name = item.get("name")
                status = item.get("status")
            except Exception:
                name, status = None, None
            if isinstance(name, str) and (isinstance(status, int) or (isinstance(status, str) and status.isdigit())):
                status_val = int(status)
                if name == "心" and heart_status is None:
                    heart_status = status_val
                elif name == "脊柱" and spine_status is None:
                    spine_status = status_val

    # 回退正则提取（同时支持双/单引号）
    if heart_status is None:
        m = re.search(r"(?:\"|')name(?:\"|')\s*:\s*(?:\"|')心(?:\"|')[^}]*?(?:\"|')status(?:\"|')\s*:\s*(\d+)", models_text, re.S)
        if m:
            heart_status = int(m.group(1))
    if spine_status is None:
        m = re.search(r"(?:\"|')name(?:\"|')\s*:\s*(?:\"|')脊柱(?:\"|')[^}]*?(?:\"|')status(?:\"|')\s*:\s*(\d+)", models_text, re.S)
        if m:
            spine_status = int(m.group(1))

    return heart_status, spine_status


def _query_by_create_time(conn: pymysql.connections.Connection, create_time: str) -> List[Dict[str, Any]]:
    sql = (
        "SELECT T_WEAR_USER_ID, source_date, create_time, models "
        "FROM andun_health.h_health_analysis WHERE create_time = %s"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (create_time,))
        rows = cur.fetchall()
    return rows or []


def main():
    args = _parse_args()
    create_time = args.create_time
    if not create_time:
        create_time = input("请输入 create_time（如 2025-11-07 12:40:01）：").strip()
        if not create_time:
            print("未提供 create_time，已退出。")
            sys.exit(1)

    try:
        conn = _connect()
    except Exception as e:
        print(f"数据库连接失败：{e}")
        sys.exit(2)

    try:
        rows = _query_by_create_time(conn, create_time)
    except Exception as e:
        print(f"查询失败：{e}")
        conn.close()
        sys.exit(3)

    if not rows:
        print(f"无记录：create_time = {create_time}")
        conn.close()
        return

    extracted: List[Dict[str, Any]] = []
    for r in rows:
        models_text = r.get("models") or ""
        heart_status, spine_status = _extract_statuses_from_models(models_text)
        extracted.append(
            {
                "wear_user_id": r.get("T_WEAR_USER_ID"),
                "source_date": r.get("source_date"),
                "create_time": r.get("create_time"),
                "heart_status": heart_status,
                "spine_status": spine_status,
            }
        )

    heart_2 = sum(1 for x in extracted if x["heart_status"] == 2)
    heart_3 = sum(1 for x in extracted if x["heart_status"] == 3)
    spine_2 = sum(1 for x in extracted if x["spine_status"] == 2)
    spine_3 = sum(1 for x in extracted if x["spine_status"] == 3)

    print(f"记录总数：{len(extracted)}（create_time={create_time}）")
    print(f"心 status=2 记录数量：{heart_2}")
    print(f"心 status=3 记录数量：{heart_3}")
    print(f"脊柱 status=2 记录数量：{spine_2}")
    print(f"脊柱 status=3 记录数量：{spine_3}")

    # 输出部分行，便于核对
    print("示例（最多前 10 行）：wear_user_id, heart_status, spine_status")
    for row in extracted[:10]:
        print(f"{row['wear_user_id']}, {row['heart_status']}, {row['spine_status']}")

    # 生成 CSV 输出
    out_csv = os.path.abspath(args.output_csv)
    try:
        import csv

        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["wear_user_id", "source_date", "create_time", "heart_status", "spine_status"])
            for row in extracted:
                w.writerow([
                    row["wear_user_id"],
                    row["source_date"],
                    row["create_time"],
                    row["heart_status"],
                    row["spine_status"],
                ])
        print(f"已写出：{out_csv}")
    except Exception as e:
        print(f"写出 CSV 失败：{e}")

    conn.close()


if __name__ == "__main__":
    main()