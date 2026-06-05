"""
医学智能体协同系统 - 核心框架
Medical Agent Orchestration System - Core Framework
"""

# ==================== 基础类型定义 ====================

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio


class AgentStatus(Enum):
    """代理状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    DECOMPOSING = "decomposing"
    SCHEDULING = "scheduling"
    RUNNING = "running"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class SkillProtocol(Enum):
    """Skill协议类型"""
    SKILLHUB = "skillhub"
    MCP = "mcp"


# ==================== 数据模型定义 ====================

@dataclass
class AgentCapability:
    """代理能力定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    priority: int = 0


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    user_id: str
    conversation_id: str
    input: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """消息定义"""
    id: str
    role: str  # user, assistant, system
    content: str
    tokens: int = 0
    agent: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    """对话定义"""
    id: str
    user_id: str
    title: str
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SkillConfig:
    """Skill配置"""
    skill_id: str
    name: str
    description: str
    protocol: SkillProtocol
    endpoint: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduledTask:
    """定时任务定义"""
    id: str
    user_id: str
    name: str
    cron_expression: str
    timezone: str
    task_content: str
    status: str = "active"
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0


# ==================== 代理基类 ====================

class BaseAgent(ABC):
    """代理基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.status = AgentStatus.IDLE
        self.capabilities: List[AgentCapability] = []
        self.llm_client: Optional[LLMClient] = None
        self.skill_gateway: Optional[SkillGateway] = None
        
    @abstractmethod
    async def initialize(self):
        """初始化代理"""
        pass
    
    @abstractmethod
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行任务"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """关闭代理"""
        pass
    
    def get_capabilities(self) -> List[AgentCapability]:
        """获取代理能力列表"""
        return self.capabilities
    
    def can_handle(self, task_type: str) -> bool:
        """判断是否能处理某类型任务"""
        return any(cap.name == task_type for cap in self.capabilities)
    
    async def call_llm(self, messages: List[Dict], **kwargs) -> Dict:
        """调用大模型"""
        if self.llm_client:
            return await self.llm_client.chat(messages, **kwargs)
        raise RuntimeError("LLM client not initialized")
    
    async def invoke_skill(self, skill_id: str, input_data: Dict) -> Dict:
        """调用Skill"""
        if self.skill_gateway:
            return await self.skill_gateway.invoke(skill_id, input_data)
        raise RuntimeError("Skill gateway not initialized")


# ==================== LLM客户端 ====================

class LLMClient:
    """大模型服务客户端（内置RAG）
    
    大模型服务地址: 192.168.0.214:8802/chat/
    该服务已内置RAG（检索增强生成）能力，包含医学知识向量库，
    可自动检索相关医学知识增强生成效果。
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.endpoint = config.get("endpoint", "http://192.168.0.214:8802/chat/")
        self.model = config.get("model", "medical-large")
        self.timeout = config.get("timeout", 30000)
        self.api_key = config.get("api_key", "")
        
    async def chat(self, messages: List[Dict], **kwargs) -> Dict:
        """发送聊天请求（自动触发RAG检索增强）
        
        大模型服务会自动：
        1. 解析用户查询意图
        2. 向量检索相关医学知识
        3. 知识增强生成响应
        4. 返回结果及知识来源引用
        """
        payload = {
            "model": self.model,
            "messages": messages,
            **kwargs
        }
        return {"content": "响应内容", "tokens": {"input": 0, "output": 0}, "sources": []}
    
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        """流式聊天（自动RAG增强）"""
        yield {"chunk": "响应", "token_count": 1}
    
    def count_tokens(self, text: str) -> int:
        """计算Token数量"""
        return len(text) // 2


# ==================== Skill网关 ====================

class SkillGateway:
    """Skill集成网关"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.skills: Dict[str, SkillConfig] = {}
        self.skillhub_client = None
        self.mcp_clients: Dict[str, Any] = {}
        
    async def register_skill(self, skill: SkillConfig):
        """注册Skill"""
        self.skills[skill.skill_id] = skill
        
    async def invoke(self, skill_id: str, input_data: Dict, **kwargs) -> Dict:
        """调用Skill"""
        if skill_id not in self.skills:
            raise ValueError(f"Skill not found: {skill_id}")
        
        skill = self.skills[skill_id]
        
        if skill.protocol == SkillProtocol.SKILLHUB:
            return await self._invoke_skillhub(skill, input_data)
        elif skill.protocol == SkillProtocol.MCP:
            return await self._invoke_mcp(skill, input_data)
        else:
            raise ValueError(f"Unknown protocol: {skill.protocol}")
    
    async def _invoke_skillhub(self, skill: SkillConfig, input_data: Dict) -> Dict:
        """调用SkillHub Skill"""
        return {"result": "SkillHub响应"}
    
    async def _invoke_mcp(self, skill: SkillConfig, input_data: Dict) -> Dict:
        """调用MCP工具"""
        return {"result": "MCP响应"}
    
    async def discover_skills(self, protocol: Optional[SkillProtocol] = None) -> List[SkillConfig]:
        """发现可用Skill"""
        if protocol:
            return [s for s in self.skills.values() if s.protocol == protocol]
        return list(self.skills.values())


# ==================== 编排代理 ====================

class OrchestratorAgent(BaseAgent):
    """编排代理"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue = asyncio.Queue()
        
    async def initialize(self):
        """初始化编排代理"""
        self.capabilities = [
            AgentCapability(
                name="task_parsing",
                description="任务解析",
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            ),
            AgentCapability(
                name="task_decomposition",
                description="任务分解",
                input_schema={"type": "object"},
                output_schema={"type": "array"}
            ),
            AgentCapability(
                name="agent_scheduling",
                description="代理调度",
                input_schema={"type": "array"},
                output_schema={"type": "object"}
            )
        ]
        
        self.llm_client = LLMClient(self.config.get("llm", {}))
        self.skill_gateway = SkillGateway(self.config.get("skill_gateway", {}))
        
    async def register_agent(self, agent: BaseAgent):
        """注册代理"""
        await agent.initialize()
        self.agents[agent.__class__.__name__] = agent
        
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行编排任务"""
        try:
            intent = await self._parse_intent(context.input)
            subtasks = await self._decompose_task(intent, context)
            schedule = await self._schedule_agents(subtasks)
            results = await self._execute_subtasks(schedule, context)
            final_result = await self._aggregate_results(results)
            
            return TaskResult(
                task_id=context.task_id,
                success=True,
                output=final_result
            )
            
        except Exception as e:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                output=None,
                error=str(e)
            )
    
    async def _parse_intent(self, user_input: str) -> Dict:
        """解析用户意图"""
        prompt = f"分析以下用户输入，识别用户意图：\n输入: {user_input}"
        response = await self.call_llm([
            {"role": "system", "content": "你是一个意图识别专家"},
            {"role": "user", "content": prompt}
        ])
        return response
    
    async def _decompose_task(self, intent: Dict, context: TaskContext) -> List[Dict]:
        """分解任务"""
        prompt = f"根据以下意图，将任务分解为子任务：\n意图: {intent}"
        response = await self.call_llm([
            {"role": "system", "content": "你是一个任务分解专家"},
            {"role": "user", "content": prompt}
        ])
        return response.get("subtasks", [])
    
    async def _schedule_agents(self, subtasks: List[Dict]) -> Dict:
        """调度代理"""
        schedule = {}
        for subtask in subtasks:
            task_type = subtask.get("task_type")
            for name, agent in self.agents.items():
                if agent.can_handle(task_type):
                    schedule[subtask["task_id"]] = agent
                    break
        return schedule
    
    async def _execute_subtasks(self, schedule: Dict, context: TaskContext) -> List[TaskResult]:
        """执行子任务"""
        results = []
        for task_id, agent in schedule.items():
            subtask_context = TaskContext(
                task_id=task_id,
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                input=context.input,
                metadata=context.metadata
            )
            result = await agent.execute(subtask_context)
            results.append(result)
        return results
    
    async def _aggregate_results(self, results: List[TaskResult]) -> Dict:
        """整合结果"""
        successful_results = [r.output for r in results if r.success]
        prompt = f"整合以下结果，生成最终响应：\n结果: {successful_results}"
        response = await self.call_llm([
            {"role": "system", "content": "你是一个结果整合专家"},
            {"role": "user", "content": prompt}
        ])
        return response
    
    async def shutdown(self):
        """关闭编排代理"""
        for agent in self.agents.values():
            await agent.shutdown()


# ==================== 诊断代理 ====================

class DiagnosisAgent(BaseAgent):
    """诊断代理"""
    
    async def initialize(self):
        """初始化诊断代理"""
        self.capabilities = [
            AgentCapability(
                name="medical_record_analysis",
                description="病历分析",
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            ),
            AgentCapability(
                name="diagnosis_suggestion",
                description="诊断建议",
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            ),
            AgentCapability(
                name="differential_diagnosis",
                description="鉴别诊断",
                input_schema={"type": "object"},
                output_schema={"type": "array"}
            )
        ]
        
        self.llm_client = LLMClient(self.config.get("llm", {}))
        
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行诊断任务"""
        task_type = context.metadata.get("task_type")
        
        if task_type == "medical_record_analysis":
            return await self._analyze_record(context)
        elif task_type == "diagnosis_suggestion":
            return await self._suggest_diagnosis(context)
        else:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                output=None,
                error=f"Unknown task type: {task_type}"
            )
    
    async def _analyze_record(self, context: TaskContext) -> TaskResult:
        """分析病历"""
        record = context.input.get("record", "")
        prompt = f"作为医学专家，分析以下病历：\n{record}"
        response = await self.call_llm([
            {"role": "system", "content": "你是一位资深临床医生"},
            {"role": "user", "content": prompt}
        ])
        return TaskResult(task_id=context.task_id, success=True, output=response)
    
    async def _suggest_diagnosis(self, context: TaskContext) -> TaskResult:
        """诊断建议"""
        symptoms = context.input.get("symptoms", [])
        prompt = f"根据以下症状给出诊断建议：\n症状: {symptoms}"
        response = await self.call_llm([
            {"role": "system", "content": "你是一位资深临床医生"},
            {"role": "user", "content": prompt}
        ])
        return TaskResult(task_id=context.task_id, success=True, output=response)
    
    async def shutdown(self):
        """关闭诊断代理"""
        pass


# ==================== Token计算器 ====================

class TokenCalculator:
    """Token计算器"""
    
    def __init__(self, model_name: str = "medical-large"):
        self.model_name = model_name
        
    def count_tokens(self, text: str) -> int:
        """计算文本Token数量"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def count_messages(self, messages: List[Dict]) -> int:
        """计算消息列表Token数量"""
        total = 0
        for msg in messages:
            total += 4
            total += self.count_tokens(msg.get("role", ""))
            total += self.count_tokens(msg.get("content", ""))
        total += 2
        return total
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, 
                      model: str = None) -> float:
        """估算成本"""
        pricing = {
            "medical-large": {"input": 0.01, "output": 0.02},
            "medical-small": {"input": 0.005, "output": 0.01}
        }
        p = pricing.get(model or self.model_name, pricing["medical-large"])
        return (input_tokens * p["input"] + output_tokens * p["output"]) / 1000


# ==================== 定时任务调度器 ====================

class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        
    async def create_task(self, task: ScheduledTask):
        """创建定时任务"""
        self.tasks[task.id] = task
        
    async def cancel_task(self, task_id: str):
        """取消定时任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            
    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取定时任务"""
        return self.tasks.get(task_id)
    
    async def list_tasks(self, user_id: str = None) -> List[ScheduledTask]:
        """列出定时任务"""
        if user_id:
            return [t for t in self.tasks.values() if t.user_id == user_id]
        return list(self.tasks.values())


# ==================== 提示词优化器 ====================

class PromptOptimizer:
    """提示词优化器"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
    async def optimize(self, prompt: str) -> Dict:
        """优化提示词"""
        analysis = await self._analyze_prompt(prompt)
        suggestions = await self._generate_suggestions(prompt, analysis)
        optimized = await self._apply_optimization(prompt, suggestions)
        
        return {
            "original": prompt,
            "optimized": optimized,
            "analysis": analysis,
            "suggestions": suggestions
        }
    
    async def _analyze_prompt(self, prompt: str) -> Dict:
        """分析提示词"""
        analysis_prompt = f"分析以下提示词的问题：\n提示词: {prompt}"
        response = await self.llm_client.chat([
            {"role": "system", "content": "你是一个提示词优化专家"},
            {"role": "user", "content": analysis_prompt}
        ])
        return response
    
    async def _generate_suggestions(self, prompt: str, analysis: Dict) -> List[str]:
        """生成优化建议"""
        return ["建议1", "建议2"]
    
    async def _apply_optimization(self, prompt: str, suggestions: List[str]) -> str:
        """应用优化"""
        optimize_prompt = f"根据以下建议优化提示词：\n原提示词: {prompt}\n建议: {suggestions}"
        response = await self.llm_client.chat([
            {"role": "system", "content": "你是一个提示词优化专家"},
            {"role": "user", "content": optimize_prompt}
        ])
        return response.get("content", prompt)


# ==================== 主程序入口 ====================

async def main():
    """主程序入口"""
    config = {
        "llm": {
            "endpoint": "http://192.168.0.214:8802/chat/",
            "model": "medical-large"
        },
        "skill_gateway": {}
    }
    
    orchestrator = OrchestratorAgent(config)
    await orchestrator.initialize()
    
    diagnosis_agent = DiagnosisAgent(config)
    await orchestrator.register_agent(diagnosis_agent)
    
    context = TaskContext(
        task_id="task_001",
        user_id="user_001",
        conversation_id="conv_001",
        input="患者主诉头痛3天，伴有发热",
        metadata={"task_type": "diagnosis_suggestion"}
    )
    
    result = await orchestrator.execute(context)
    print(f"任务结果: {result}")
    
    await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
