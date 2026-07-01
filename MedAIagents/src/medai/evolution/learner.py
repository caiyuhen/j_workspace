"""
反馈收集器
基于 SQLite 存储用户反馈，支持按任务类型查询与统计
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional


class FeedbackCollector:
    def __init__(self, memory_system=None, db_path='./data/feedback.db'):
        self.memory_system = memory_system
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    input_text TEXT,
                    output_text TEXT,
                    feedback TEXT,
                    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def record_feedback(self, task_id: str, task_type: str, input_text: str,
                        output_text: str, feedback: str, rating: int):
        """记录一条用户反馈

        Args:
            task_id: 任务唯一标识
            task_type: 任务类型，如 'diagnosis', 'summary'
            input_text: 输入文本
            output_text: 模型输出文本
            feedback: 用户文字反馈
            rating: 1-5 星评分
        """
        if not (1 <= rating <= 5):
            raise ValueError("rating must be between 1 and 5")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''INSERT INTO feedback (task_id, task_type, input_text, output_text, feedback, rating)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (task_id, task_type, input_text, output_text, feedback, rating)
            )
            conn.commit()

        if self.memory_system:
            self.memory_system.store({
                'type': 'feedback',
                'task_id': task_id,
                'task_type': task_type,
                'feedback': feedback,
                'rating': rating
            })

    def get_feedback_history(self, task_type: str = None, limit: int = 100) -> List[Dict]:
        """获取反馈历史

        Args:
            task_type: 按任务类型筛选，None 表示全部
            limit: 返回条数上限

        Returns:
            反馈记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if task_type:
                rows = conn.execute(
                    '''SELECT * FROM feedback WHERE task_type = ? ORDER BY created_at DESC LIMIT ?''',
                    (task_type, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    '''SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?''',
                    (limit,)
                ).fetchall()
            return [dict(row) for row in rows]

    def get_average_rating(self, task_type: str = None) -> float:
        """获取平均评分

        Args:
            task_type: 按任务类型筛选，None 表示全部

        Returns:
            平均评分，无记录时返回 0.0
        """
        with sqlite3.connect(self.db_path) as conn:
            if task_type:
                row = conn.execute(
                    '''SELECT AVG(rating) as avg_rating FROM feedback WHERE task_type = ?''',
                    (task_type,)
                ).fetchone()
            else:
                row = conn.execute(
                    '''SELECT AVG(rating) as avg_rating FROM feedback'''
                ).fetchone()
            return row[0] if row[0] is not None else 0.0

    def get_common_issues(self, task_type: str = None) -> List[str]:
        """获取常见问题反馈

        通过关键词匹配提取包含负面情绪的反馈。

        Args:
            task_type: 按任务类型筛选，None 表示全部

        Returns:
            问题反馈文本列表，最多 20 条
        """
        history = self.get_feedback_history(task_type=task_type, limit=500)
        issues = []
        keywords = ['错误', '问题', '不好', '失败', '不准确', '差',
                    'bug', 'error', 'wrong', 'bad', 'issue', 'fail', 'incorrect']
        for item in history:
            feedback = item.get('feedback', '') or ''
            if feedback and len(feedback) >= 2:
                if any(kw in feedback.lower() for kw in keywords):
                    issues.append(feedback.strip())
        return issues[:20]
