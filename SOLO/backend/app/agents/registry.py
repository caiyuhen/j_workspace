"""
代理注册中心

管理所有代理的注册、发现和生命周期
"""
from typing import Dict, List, Optional
from app.agents.base import BaseAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.research import ResearchAgent
from app.agents.consultation import ConsultationAgent
from app.agents.knowledge import KnowledgeAgent
from app.agents.tool import ToolAgent
from app.agents.quality import QualityAgent
from app.agents.learning import LearningAgent


class AgentRegistry:
    """
    代理注册中心（单例模式）
    
    负责：
    - 代理的注册和管理
    - 编排代理的初始化
    - 代理发现
    
    已注册代理：
    - orchestrator: 编排代理（核心大脑）
    - diagnosis: 诊断代理（临床诊断辅助）
    - research: 研究代理（医学研究助手）
    - consultation: 咨询代理（健康咨询顾问）
    - knowledge: 知识代理（医学知识查询）
    - tool: 工具代理（Skill集成）
    - quality: 质控代理（质量与安全）
    - learning: 学习代理（系统进化）
    """
    
    _instance: Optional['AgentRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.agents: Dict[str, BaseAgent] = {}
        self.orchestrator: Optional[OrchestratorAgent] = None
        
        # 初始化所有代理
        self._setup_agents()
    
    def _setup_agents(self):
        """初始化所有代理"""
        # ========== 1. 创建编排代理（核心大脑）==========
        self.orchestrator = OrchestratorAgent()
        self.orchestrator.display_name = "编排代理"
        self.agents["orchestrator"] = self.orchestrator
        
        # ========== 2. 创建专业代理 ==========
        
        # 诊断代理 - 临床诊断辅助
        diagnosis_agent = DiagnosisAgent()
        diagnosis_agent.display_name = "诊断代理"
        self.agents["diagnosis"] = diagnosis_agent
        
        # 研究代理 - 医学研究助手
        research_agent = ResearchAgent()
        research_agent.display_name = "研究代理"
        self.agents["research"] = research_agent
        
        # 咨询代理 - 健康咨询顾问
        consultation_agent = ConsultationAgent()
        consultation_agent.display_name = "咨询代理"
        self.agents["consultation"] = consultation_agent
        
        # 知识代理 - 医学知识查询
        knowledge_agent = KnowledgeAgent()
        knowledge_agent.display_name = "知识代理"
        self.agents["knowledge"] = knowledge_agent
        
        # 工具代理 - Skill集成
        tool_agent = ToolAgent()
        tool_agent.display_name = "工具代理"
        self.agents["tool"] = tool_agent
        
        # 质控代理 - 质量与安全
        quality_agent = QualityAgent()
        quality_agent.display_name = "质控代理"
        self.agents["quality"] = quality_agent
        
        # 学习代理 - 系统进化
        learning_agent = LearningAgent()
        learning_agent.display_name = "学习代理"
        self.agents["learning"] = learning_agent
        
        # ========== 3. 将专业代理注册到编排代理 ==========
        # 编排代理可调度所有专业代理
        self.orchestrator.register_agent(diagnosis_agent)
        self.orchestrator.register_agent(research_agent)
        self.orchestrator.register_agent(consultation_agent)
        self.orchestrator.register_agent(knowledge_agent)
        self.orchestrator.register_agent(tool_agent)
        # 质控/学习也注册到编排代理，便于统一路由（task_type 通过 capabilities 映射）
        self.orchestrator.register_agent(quality_agent)
        self.orchestrator.register_agent(learning_agent)
    
    def register_agent(self, agent: BaseAgent):
        """
        注册新代理
        
        Args:
            agent: 代理实例
        """
        self.agents[agent.name] = agent
        if self.orchestrator:
            self.orchestrator.register_agent(agent)
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        注销代理
        
        Args:
            agent_name: 代理名称
            
        Returns:
            bool: 是否成功注销
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            if self.orchestrator:
                self.orchestrator.unregister_agent(agent_name)
            return True
        return False
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        获取代理
        
        Args:
            name: 代理名称
            
        Returns:
            BaseAgent: 代理实例，不存在则返回None
        """
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """
        列出所有已注册的代理名称
        
        Returns:
            List[str]: 代理名称列表
        """
        return list(self.agents.keys())
    
    def get_agent_info(self, name: str) -> Optional[Dict]:
        """
        获取代理详细信息
        
        Args:
            name: 代理名称
            
        Returns:
            Dict: 代理信息
        """
        agent = self.agents.get(name)
        if not agent:
            return None
        
        return {
            "name": agent.name,
            "display_name": getattr(agent, 'display_name', agent.name),
            "description": agent.description,
            "capabilities": agent.capabilities,
            "status": agent.status.value
        }
    
    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """
        按能力查找代理
        
        Args:
            capability: 能力名称
            
        Returns:
            List[BaseAgent]: 具有该能力的代理列表
        """
        return [
            agent for agent in self.agents.values()
            if agent.can_handle(capability)
        ]
    
    def get_all_capabilities(self) -> Dict[str, List[str]]:
        """
        获取所有代理的能力映射
        
        Returns:
            Dict[str, List[str]]: 代理名称 -> 能力列表
        """
        return {
            name: agent.capabilities
            for name, agent in self.agents.items()
        }


# 全局单例实例
agent_registry = AgentRegistry()
