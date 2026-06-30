"""
记忆系统模块
Memory System Module
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger

from ..config import Config


class MemorySystem:
    """记忆系统 - 支持跨会话持久化记忆"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.memory_config = self.config.get('memory', {})
        self.provider = self.memory_config.get('provider', 'sqlite')
        self.storage_path = self.memory_config.get('storage_path', './data/memory')
        
        # 确保存储目录存在
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 初始化存储后端
        self._init_storage()
        
        # 加载当前会话
        self.current_session_id = None
        self.session_messages: List[Dict[str, Any]] = []
        
        # 用户偏好
        self.user_preferences: Dict[str, Any] = {}
        self._load_user_preferences()
    
    def _init_storage(self):
        """初始化存储后端"""
        if self.provider == 'sqlite':
            self._init_sqlite()
    
    def _init_sqlite(self):
        """初始化SQLite数据库"""
        db_path = os.path.join(self.storage_path, 'memory.db')
        
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # 创建会话历史表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP,
                    last_updated TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # 创建消息表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # 创建用户偏好表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP
                )
            ''')
            
            # 创建任务经验表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_experience (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT,
                    description TEXT,
                    outcome TEXT,
                    learned_lesson TEXT,
                    created_at TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info("SQLite memory storage initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite memory: {e}")
            raise
    
    def _load_user_preferences(self):
        """加载用户偏好"""
        if self.provider == 'sqlite':
            self.cursor.execute('SELECT key, value FROM user_preferences')
            rows = self.cursor.fetchall()
            for key, value in rows:
                try:
                    self.user_preferences[key] = json.loads(value)
                except:
                    self.user_preferences[key] = value
    
    # ==================== 会话管理 ====================
    
    def create_session(self, metadata: Dict[str, Any] = None) -> str:
        """创建新会话
        
        Args:
            metadata: 会话元数据
        
        Returns:
            会话ID
        """
        import uuid
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        if self.provider == 'sqlite':
            self.cursor.execute(
                'INSERT INTO sessions (session_id, created_at, last_updated, metadata) VALUES (?, ?, ?, ?)',
                (session_id, now, now, json.dumps(metadata or {}))
            )
            self.conn.commit()
        
        self.current_session_id = session_id
        self.session_messages = []
        logger.info(f"Created new session: {session_id}")
        
        return session_id
    
    def switch_session(self, session_id: str):
        """切换会话
        
        Args:
            session_id: 会话ID
        """
        self.current_session_id = session_id
        
        # 加载会话消息
        if self.provider == 'sqlite':
            self.cursor.execute(
                'SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id',
                (session_id,)
            )
            rows = self.cursor.fetchall()
            self.session_messages = [
                {'role': row[0], 'content': row[1], 'timestamp': row[2]}
                for row in rows
            ]
        
        logger.info(f"Switched to session: {session_id}")
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """添加消息到当前会话
        
        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 消息元数据
        """
        if not self.current_session_id:
            self.create_session()
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        self.session_messages.append(message)
        
        # 持久化存储
        if self.provider == 'sqlite':
            self.cursor.execute(
                'INSERT INTO messages (session_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)',
                (
                    self.current_session_id,
                    role,
                    content,
                    message['timestamp'],
                    json.dumps(metadata or {})
                )
            )
            # 更新会话最后更新时间
            self.cursor.execute(
                'UPDATE sessions SET last_updated = ? WHERE session_id = ?',
                (datetime.now().isoformat(), self.current_session_id)
            )
            self.conn.commit()
    
    def get_conversation_history(self, limit: int = None) -> List[Dict[str, str]]:
        """获取对话历史（用于LLM上下文）
        
        Args:
            limit: 限制消息数量
        
        Returns:
            消息列表（仅包含role和content）
        """
        messages = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in self.session_messages
        ]
        
        if limit:
            return messages[-limit:]
        return messages
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """列出所有会话
        
        Args:
            limit: 限制数量
        
        Returns:
            会话列表
        """
        if self.provider == 'sqlite':
            self.cursor.execute(
                'SELECT session_id, created_at, last_updated, metadata FROM sessions ORDER BY last_updated DESC LIMIT ?',
                (limit,)
            )
            rows = self.cursor.fetchall()
            
            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row[0],
                    'created_at': row[1],
                    'last_updated': row[2],
                    'metadata': json.loads(row[3]) if row[3] else {}
                })
            return sessions
        
        return []
    
    # ==================== 用户偏好管理 ====================
    
    def set_preference(self, key: str, value: Any):
        """设置用户偏好
        
        Args:
            key: 偏好键
            value: 偏好值
        """
        self.user_preferences[key] = value
        
        if self.provider == 'sqlite':
            self.cursor.execute(
                '''REPLACE INTO user_preferences (key, value, updated_at) VALUES (?, ?, ?)''',
                (key, json.dumps(value), datetime.now().isoformat())
            )
            self.conn.commit()
        
        logger.debug(f"Set preference: {key} = {value}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好
        
        Args:
            key: 偏好键
            default: 默认值
        
        Returns:
            偏好值
        """
        return self.user_preferences.get(key, default)
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """获取所有用户偏好"""
        return self.user_preferences.copy()
    
    # ==================== 任务经验管理 ====================
    
    def add_task_experience(
        self,
        task_type: str,
        description: str,
        outcome: str,
        learned_lesson: str
    ):
        """记录任务经验
        
        Args:
            task_type: 任务类型
            description: 任务描述
            outcome: 任务结果
            learned_lesson: 经验教训
        """
        if self.provider == 'sqlite':
            self.cursor.execute(
                '''INSERT INTO task_experience 
                   (task_type, description, outcome, learned_lesson, created_at) 
                   VALUES (?, ?, ?, ?, ?)''',
                (task_type, description, outcome, learned_lesson, datetime.now().isoformat())
            )
            self.conn.commit()
        
        logger.info(f"Recorded task experience: {task_type}")
    
    def get_task_experience(self, task_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务经验
        
        Args:
            task_type: 任务类型（可选）
            limit: 限制数量
        
        Returns:
            经验列表
        """
        if self.provider == 'sqlite':
            if task_type:
                self.cursor.execute(
                    '''SELECT task_type, description, outcome, learned_lesson, created_at 
                       FROM task_experience WHERE task_type = ? ORDER BY created_at DESC LIMIT ?''',
                    (task_type, limit)
                )
            else:
                self.cursor.execute(
                    '''SELECT task_type, description, outcome, learned_lesson, created_at 
                       FROM task_experience ORDER BY created_at DESC LIMIT ?''',
                    (limit,)
                )
            
            rows = self.cursor.fetchall()
            return [
                {
                    'task_type': row[0],
                    'description': row[1],
                    'outcome': row[2],
                    'learned_lesson': row[3],
                    'created_at': row[4]
                }
                for row in rows
            ]
        
        return []
    
    # ==================== 上下文压缩 ====================
    
    def compress_context(self, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """压缩对话上下文，确保不超过token限制
        
        Args:
            max_tokens: 最大token数
        
        Returns:
            压缩后的消息列表
        """
        messages = self.get_conversation_history()
        
        # 简单的基于数量的压缩（保留system消息，然后保留最新的对话）
        system_messages = [m for m in messages if m['role'] == 'system']
        conversation_messages = [m for m in messages if m['role'] != 'system']
        
        # 估算token数量（简单估算：每个token约4个字符）
        estimated_tokens = sum(len(m['content']) // 4 for m in messages)
        
        if estimated_tokens <= max_tokens:
            return messages
        
        # 需要压缩，逐步移除旧消息
        while len(conversation_messages) > 2:
            # 移除最早的一轮对话
            conversation_messages.pop(0)  # user
            if conversation_messages:
                conversation_messages.pop(0)  # assistant
            
            remaining = system_messages + conversation_messages
            estimated_tokens = sum(len(m['content']) // 4 for m in remaining)
            
            if estimated_tokens <= max_tokens:
                break
        
        return system_messages + conversation_messages
    
    def close(self):
        """关闭记忆系统"""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("Memory system closed")
