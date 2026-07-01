"""
性能追踪器
基于 SQLite 存储任务执行性能数据，支持生成周期报告
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional


class PerformanceTracker:
    def __init__(self, db_path='./data/performance.db'):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    token_usage TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def record_execution(self, task_type: str, duration_ms: int, success: bool,
                         token_usage: Dict = None):
        """记录一次任务执行

        Args:
            task_type: 任务类型
            duration_ms: 执行耗时（毫秒）
            success: 是否成功
            token_usage: Token 使用量字典，如 {'prompt_tokens': 100, 'completion_tokens': 50}
        """
        token_usage_json = json.dumps(token_usage) if token_usage else None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''INSERT INTO performance (task_type, duration_ms, success, token_usage)
                   VALUES (?, ?, ?, ?)''',
                (task_type, duration_ms, success, token_usage_json)
            )
            conn.commit()

    def get_performance_report(self, days: int = 7) -> Dict:
        """获取周期性能报告

        Args:
            days: 统计最近 N 天

        Returns:
            报告字典，包含 total_tasks, success_rate, avg_duration_ms, token_usage
        """
        since = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            total = conn.execute(
                '''SELECT COUNT(*) as cnt FROM performance WHERE created_at >= ?''',
                (since,)
            ).fetchone()['cnt']

            success_row = conn.execute(
                '''SELECT COUNT(*) as cnt FROM performance WHERE success = 1 AND created_at >= ?''',
                (since,)
            ).fetchone()
            success_count = success_row['cnt'] if success_row else 0

            avg_duration_row = conn.execute(
                '''SELECT AVG(duration_ms) as avg_dur FROM performance WHERE created_at >= ?''',
                (since,)
            ).fetchone()
            avg_duration = avg_duration_row['avg_dur'] if avg_duration_row and avg_duration_row['avg_dur'] else 0

            token_rows = conn.execute(
                '''SELECT token_usage FROM performance WHERE token_usage IS NOT NULL AND created_at >= ?''',
                (since,)
            ).fetchall()

            total_tokens = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            token_count = 0
            for row in token_rows:
                try:
                    usage = json.loads(row['token_usage'])
                    for key in total_tokens:
                        if key in usage:
                            total_tokens[key] += usage[key]
                    token_count += 1
                except (json.JSONDecodeError, TypeError):
                    continue

            return {
                'total_tasks': total,
                'success_rate': success_count / total if total > 0 else 0.0,
                'avg_duration_ms': round(avg_duration, 2) if avg_duration else 0,
                'token_usage': total_tokens if token_count > 0 else None
            }
