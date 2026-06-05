"""
代理模块

包含所有专业代理的实现
"""
from app.agents.base import BaseAgent, TaskContext, TaskResult, AgentStatus
from app.agents.orchestrator import OrchestratorAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.research import ResearchAgent
from app.agents.consultation import ConsultationAgent
from app.agents.knowledge import KnowledgeAgent
from app.agents.tool import ToolAgent
from app.agents.quality import QualityAgent
from app.agents.learning import LearningAgent
from app.agents.registry import agent_registry

__all__ = [
    # 基类
    "BaseAgent",
    "TaskContext",
    "TaskResult",
    "AgentStatus",
    
    # 专业代理
    "OrchestratorAgent",
    "DiagnosisAgent",
    "ResearchAgent",
    "ConsultationAgent",
    "KnowledgeAgent",
    "ToolAgent",
    "QualityAgent",
    "LearningAgent",
    
    # 注册中心
    "agent_registry"
]
