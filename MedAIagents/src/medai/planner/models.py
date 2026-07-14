"""
任务规划器数据模型
Task Planner Data Models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SubTask(BaseModel):
    """子任务模型"""

    id: str
    description: str
    tool: Optional[str] = None
    arguments: Dict[str, Any] = {}
    dependencies: List[str] = []  # 依赖的其他子任务 id
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        """初始化后处理：确保 id 不在自己的依赖中"""
        if self.id in self.dependencies:
            self.dependencies = [dep for dep in self.dependencies if dep != self.id]


class TaskPlan(BaseModel):
    """任务计划模型"""

    goal: str
    subtasks: List[SubTask]
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    replan_count: int = 0  # 重规划次数

    def get_subtask(self, subtask_id: str) -> Optional[SubTask]:
        """根据 id 获取子任务"""
        for st in self.subtasks:
            if st.id == subtask_id:
                return st
        return None

    def is_completed(self) -> bool:
        """检查所有子任务是否已完成"""
        return all(
            st.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            for st in self.subtasks
        )

    def reset(self) -> None:
        """重置所有子任务状态为 PENDING"""
        for st in self.subtasks:
            st.status = TaskStatus.PENDING
            st.result = None
            st.error = None
        self.completed_at = None
