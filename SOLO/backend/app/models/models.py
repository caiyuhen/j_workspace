"""
数据库模型定义
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.core.database import Base


def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RESEARCHER = "researcher"
    USER = "user"


class ConversationStatus(str, enum.Enum):
    """对话状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, enum.Enum):
    """代理类型枚举"""
    ORCHESTRATOR = "orchestrator"
    DIAGNOSIS = "diagnosis"
    RESEARCH = "research"
    CONSULTATION = "consultation"
    KNOWLEDGE = "knowledge"
    TOOL = "tool"
    QUALITY = "quality"
    LEARNING = "learning"


# ============== 用户模型 ==============

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    avatar = Column(String(500), nullable=True)
    department = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # 关系
    conversations = relationship("Conversation", back_populates="user", lazy="dynamic")
    tasks = relationship("Task", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User {self.email}>"


# ============== 对话模型 ==============

class Conversation(Base):
    """对话表"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    
    # 对话上下文
    context = Column(JSON, default=dict)
    
    # 统计信息
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", lazy="dynamic", 
                          cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="conversation", lazy="dynamic")
    
    def __repr__(self):
        return f"<Conversation {self.id}>"


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # 消息内容
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # 元数据
    agent_type = Column(Enum(AgentType), nullable=True)
    tokens = Column(Integer, default=0)
    metadata = Column(JSON, default=dict)
    
    # 引用的知识
    references = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} [{self.role}]>"


# ============== 任务模型 ==============

class Task(Base):
    """任务表"""
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True, index=True)
    
    # 任务信息
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)  # diagnosis, research, consultation, etc.
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    
    # 任务配置
    config = Column(JSON, default=dict)
    
    # 执行结果
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 代理分配
    assigned_agents = Column(JSON, default=list)
    
    # 时间统计
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="tasks")
    conversation = relationship("Conversation", back_populates="tasks")
    subtasks = relationship("SubTask", back_populates="task", lazy="dynamic",
                          cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task {self.id} [{self.status}]>"


class SubTask(Base):
    """子任务表"""
    __tablename__ = "subtasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    
    # 子任务信息
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    agent_type = Column(Enum(AgentType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    
    # 执行信息
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 依赖关系
    depends_on = Column(JSON, default=list)  # 子任务ID列表
    
    # 时间统计
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    task = relationship("Task", back_populates="subtasks")
    
    def __repr__(self):
        return f"<SubTask {self.id} [{self.agent_type}]>"


# ============== 技能模型 ==============

class Skill(Base):
    """技能表"""
    __tablename__ = "skills"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # 技能信息
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    
    # 协议类型
    protocol = Column(String(20), nullable=False)  # skillhub, mcp
    
    # 配置
    config = Column(JSON, default=dict)
    input_schema = Column(JSON, default=dict)
    output_schema = Column(JSON, default=dict)
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_builtin = Column(Boolean, default=False, nullable=False)
    
    # 统计
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Skill {self.name}>"


# ============== 知识库模型 ==============

class KnowledgeItem(Base):
    """知识条目表（用于缓存LLM返回的知识）"""
    __tablename__ = "knowledge_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # 知识信息
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    category = Column(String(50), nullable=True, index=True)
    
    # 标签
    tags = Column(JSON, default=list)
    
    # 向量ID（如果需要）
    vector_id = Column(String(100), nullable=True)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<KnowledgeItem {self.id}>"


# ============== 系统日志模型 ==============

class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # 日志信息
    level = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)  # 模块名
    
    # 上下文
    user_id = Column(String(36), nullable=True, index=True)
    conversation_id = Column(String(36), nullable=True, index=True)
    task_id = Column(String(36), nullable=True, index=True)
    
    # 详细信息
    details = Column(JSON, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<SystemLog {self.level}: {self.message[:50]}>"
