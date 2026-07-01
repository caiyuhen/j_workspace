# MedAIagents v0.6.0 Agent 基础设施全量补齐计划

> **目标:** 将 MedAIagents 从领域专用框架升级为具备现代 Agent 基础设施的医学 AI 平台

**架构:** 采用分层架构 — 底层 MCP 协议适配器 + 工具层医学功能封装 + 规划层任务编排 + 协作层多 Agent 通信

**技术栈:** Python, MCP SDK (stdio/sse), FastAPI, Pydantic, asyncio

---

## 模块一: MCP Client 集成

### Task 1.1: MCP 核心协议适配器

**文件:**
- Create: `src/medai/mcp/__init__.py`
- Create: `src/medai/mcp/client.py`
- Create: `src/medai/mcp/server_manager.py`
- Create: `src/medai/mcp/types.py`
- Create: `tests/test_mcp_client.py`

**步骤:**

- [ ] **Step 1: 定义 MCP 类型系统**

```python
# src/medai/mcp/types.py
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel

class MCPTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class MCPResource(BaseModel):
    uri: str
    name: str
    mime_type: Optional[str] = None

class MCPPrompt(BaseModel):
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = None

class MCPCallToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}

class MCPCallToolResult(BaseModel):
    content: List[Dict[str, Any]]
    is_error: bool = False
```

- [ ] **Step 2: 实现 MCPClient 基类**

```python
# src/medai/mcp/client.py
import asyncio
import json
from typing import Dict, List, Any, Optional
from .types import MCPTool, MCPResource, MCPPrompt, MCPCallToolRequest, MCPCallToolResult

class MCPClient:
    """MCP 客户端基类 - 支持 stdio 和 sse 传输"""
    
    def __init__(self, name: str, transport: Literal["stdio", "sse"] = "stdio"):
        self.name = name
        self.transport = transport
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        self.prompts: List[MCPPrompt] = []
        self._connected = False
    
    async def connect(self, command: str = None, args: List[str] = None, 
                      url: str = None) -> bool:
        """连接到 MCP Server"""
        pass
    
    async def list_tools(self) -> List[MCPTool]:
        """获取 Server 提供的工具列表"""
        pass
    
    async def call_tool(self, request: MCPCallToolRequest) -> MCPCallToolResult:
        """调用工具"""
        pass
    
    async def disconnect(self):
        """断开连接"""
        pass
```

- [ ] **Step 3: 实现 stdio 传输**

实现基于子进程 stdin/stdout 的 MCP 通信协议。

- [ ] **Step 4: 实现 sse 传输**

实现基于 HTTP Server-Sent Events 的 MCP 通信协议。

- [ ] **Step 5: 实现 MCPServerManager**

```python
# src/medai/mcp/server_manager.py
class MCPServerManager:
    """管理多个 MCP Server 连接"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self._all_tools: Dict[str, MCPTool] = {}
    
    async def add_server(self, name: str, config: Dict[str, Any]) -> bool:
        """添加并连接 MCP Server"""
        pass
    
    async def remove_server(self, name: str):
        """移除 MCP Server"""
        pass
    
    def get_all_tools(self) -> List[MCPTool]:
        """获取所有 Server 的工具列表"""
        pass
    
    async def call_tool(self, server_name: str, tool_name: str, 
                        arguments: Dict[str, Any]) -> MCPCallToolResult:
        """调用指定 Server 的工具"""
        pass
```

- [ ] **Step 6: 编写测试**

```python
# tests/test_mcp_client.py
import pytest
from medai.mcp.types import MCPTool, MCPCallToolRequest
from medai.mcp.client import MCPClient
from medai.mcp.server_manager import MCPServerManager

class TestMCPClient:
    def test_tool_creation(self):
        tool = MCPTool(name="diagnose", description="诊断", input_schema={})
        assert tool.name == "diagnose"
    
    @pytest.mark.asyncio
    async def test_server_manager(self):
        manager = MCPServerManager()
        assert len(manager.get_all_tools()) == 0
```

---

## 模块二: 工具调用框架 (Function Calling)

### Task 2.1: 医学工具定义与注册

**文件:**
- Create: `src/medai/tools/__init__.py`
- Create: `src/medai/tools/registry.py`
- Create: `src/medai/tools/medical_tools.py`
- Create: `src/medai/tools/executor.py`
- Create: `tests/test_tools.py`

**步骤:**

- [ ] **Step 1: 定义工具注册表**

```python
# src/medai/tools/registry.py
from typing import Dict, List, Callable, Any
from pydantic import BaseModel

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable = None
    
    class Config:
        arbitrary_types_allowed = True

class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, name: str, description: str, parameters: Dict[str, Any], 
                 func: Callable = None):
        """注册工具"""
        self._tools[name] = ToolDefinition(
            name=name, description=description, 
            parameters=parameters, func=func
        )
    
    def get(self, name: str) -> ToolDefinition:
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """返回 OpenAI Function Calling 格式的工具列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters
                }
            }
            for t in self._tools.values()
        ]
```

- [ ] **Step 2: 定义医学领域工具集**

将现有功能封装为工具：
- `diagnose` - 临床诊断
- `analyze_imaging` - 影像分析
- `search_literature` - 文献检索
- `calculate_sample_size` - 样本量计算
- `generate_medical_note` - 病历生成
- `check_medication_safety` - 用药安全检查
- `export_document` - 文档导出
- `execute_bioinformatics` - 生物信息学分析

- [ ] **Step 3: 实现工具执行器**

```python
# src/medai/tools/executor.py
class ToolExecutor:
    """工具执行器 - 解析 LLM 的工具调用请求并执行"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具调用"""
        tool = self.registry.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        if tool.func:
            return await tool.func(**arguments) if asyncio.iscoroutinefunction(tool.func) else tool.func(**arguments)
        raise ValueError(f"Tool '{tool_name}' has no executable function")
```

---

## 模块三: 任务规划器 (Task Planner)

### Task 3.1: 任务分解与执行引擎

**文件:**
- Create: `src/medai/planner/__init__.py`
- Create: `src/medai/planner/models.py`
- Create: `src/medai/planner/engine.py`
- Create: `tests/test_planner.py`

**步骤:**

- [ ] **Step 1: 定义任务模型**

```python
# src/medai/planner/models.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SubTask(BaseModel):
    id: str
    description: str
    tool: Optional[str] = None
    arguments: Dict[str, Any] = {}
    dependencies: List[str] = []
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None

class TaskPlan(BaseModel):
    goal: str
    subtasks: List[SubTask]
```

- [ ] **Step 2: 实现规划引擎**

```python
# src/medai/planner/engine.py
class TaskPlanner:
    """任务规划器 - 将用户请求分解为可执行的子任务"""
    
    def __init__(self, llm_router):
        self.llm = llm_router
    
    async def plan(self, user_request: str, available_tools: List[Dict]) -> TaskPlan:
        """根据用户请求和可用工具生成任务计划"""
        prompt = self._build_planning_prompt(user_request, available_tools)
        response = await self.llm.chat(messages=[{"role": "user", "content": prompt}])
        return self._parse_plan(response)
    
    async def execute(self, plan: TaskPlan, executor) -> Dict[str, Any]:
        """执行任务计划"""
        results = {}
        for task in plan.subtasks:
            if task.tool:
                task.status = TaskStatus.RUNNING
                try:
                    task.result = await executor.execute(task.tool, task.arguments)
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
            results[task.id] = task.result
        return results
```

---

## 模块四: 多 Agent 编排 (Multi-Agent Orchestration)

### Task 4.1: Agent 定义与编排引擎

**文件:**
- Create: `src/medai/agents/__init__.py`
- Create: `src/medai/agents/base.py`
- Create: `src/medai/agents/specialized.py`
- Create: `src/medai/agents/orchestrator.py`
- Create: `tests/test_agents.py`

**步骤:**

- [ ] **Step 1: 定义 Agent 基类**

```python
# src/medai/agents/base.py
class BaseAgent:
    """Agent 基类"""
    
    def __init__(self, name: str, role: str, system_prompt: str = ""):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.memory = []
    
    async def run(self, task: str, context: Dict = None) -> str:
        """执行子任务并返回结果"""
        pass
```

- [ ] **Step 2: 定义专科 Agent**

```python
# src/medai/agents/specialized.py
class ClinicalAgent(BaseAgent):
    """临床诊断 Agent"""
    pass

class ImagingAgent(BaseAgent):
    """医学影像分析 Agent"""
    pass

class ResearchAgent(BaseAgent):
    """科研辅助 Agent"""
    pass

class WritingAgent(BaseAgent):
    """医学写作 Agent"""
    pass
```

- [ ] **Step 3: 实现编排器**

```python
# src/medai/agents/orchestrator.py
class AgentOrchestrator:
    """Agent 编排器 - 协调多个专科 Agent 协作"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_bus: List[Dict] = []
    
    def register_agent(self, agent: BaseAgent):
        self.agents[agent.name] = agent
    
    async def delegate(self, task: str, required_roles: List[str]) -> Dict[str, str]:
        """将任务分派给多个 Agent 并行执行"""
        results = {}
        for role in required_roles:
            agent = self._find_agent_by_role(role)
            if agent:
                results[agent.name] = await agent.run(task)
        return results
    
    async def collaborate(self, task: str, agent_sequence: List[str]) -> str:
        """按顺序让多个 Agent 协作完成复杂任务"""
        context = {}
        for agent_name in agent_sequence:
            agent = self.agents.get(agent_name)
            if agent:
                result = await agent.run(task, context)
                context[agent_name] = result
        return self._synthesize_results(context)
```

---

## 模块五: 代码执行沙箱 (Code Sandbox)

### Task 5.1: 安全代码执行环境

**文件:**
- Create: `src/medai/sandbox/__init__.py`
- Create: `src/medai/sandbox/executor.py`
- Create: `src/medai/sandbox/security.py`
- Create: `tests/test_sandbox.py`

**步骤:**

- [ ] **Step 1: 实现受限 Python 执行器**

```python
# src/medai/sandbox/executor.py
import subprocess
import tempfile
import os

class CodeSandbox:
    """代码执行沙箱 - 安全执行 Python/Shell 代码"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.allowed_modules = [
            'numpy', 'pandas', 'matplotlib', 'scipy', 'sklearn',
            'statistics', 'json', 'math', 'random', 'datetime'
        ]
    
    def execute_python(self, code: str) -> Dict[str, Any]:
        """在受限环境中执行 Python 代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self._wrap_code(code))
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True, text=True,
                timeout=self.timeout
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        finally:
            os.unlink(temp_file)
```

---

## 模块六: 自进化机制 (Self-Evolution)

### Task 6.1: 学习与优化系统

**文件:**
- Create: `src/medai/evolution/__init__.py`
- Create: `src/medai/evolution/learner.py`
- Create: `src/medai/evolution/optimizer.py`
- Create: `tests/test_evolution.py`

**步骤:**

- [ ] **Step 1: 实现反馈收集器**

```python
# src/medai/evolution/learner.py
class FeedbackCollector:
    """收集用户反馈用于模型优化"""
    
    def __init__(self, memory_system):
        self.memory = memory_system
    
    def record_feedback(self, task_id: str, feedback: str, rating: int):
        """记录用户反馈"""
        pass
```

- [ ] **Step 2: 实现提示词优化器**

```python
# src/medai/evolution/optimizer.py
class PromptOptimizer:
    """基于反馈自动优化提示词"""
    
    def __init__(self, llm_router):
        self.llm = llm_router
    
    async def optimize_prompt(self, original_prompt: str, feedback_history: List[Dict]) -> str:
        """优化提示词"""
        pass
```

---

## 模块七: LLM 路由增强

### Task 7.1: 支持 Function Calling

**文件:**
- Modify: `src/medai/llm/routing.py`

**步骤:**

- [ ] **Step 1: 增强 OpenAIProvider 支持 tools 参数**

修改 `chat_completion` 和 `chat_completion_stream` 方法，支持传入 `tools` 参数。

- [ ] **Step 2: 添加工具调用响应解析**

```python
def parse_tool_calls(response) -> List[Dict]:
    """从 LLM 响应中解析工具调用请求"""
    pass
```

---

## 模块八: 集成与入口

### Task 8.1: 增强 MedicalAgent

**文件:**
- Modify: `src/medai/agent.py`
- Modify: `src/medai/__init__.py`

**步骤:**

- [ ] **Step 1: 在 MedicalAgent 中集成新组件**

```python
class MedicalAgent:
    def __init__(self, ...):
        # 现有初始化...
        
        # 新增 Agent 基础设施
        self.mcp_manager = MCPServerManager()
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        self.task_planner = TaskPlanner(self.llm_router)
        self.agent_orchestrator = AgentOrchestrator()
        self.code_sandbox = CodeSandbox()
        
        # 注册内置医学工具
        self._register_medical_tools()
        # 注册专科 Agent
        self._register_specialized_agents()
    
    async def chat_with_tools(self, user_input: str) -> str:
        """支持工具调用的对话模式"""
        pass
```

- [ ] **Step 2: 更新 __init__.py 导出**

---

## 测试策略

每个模块完成后运行单元测试，全部完成后运行集成测试。

```bash
pytest tests/test_mcp_client.py -v
pytest tests/test_tools.py -v
pytest tests/test_planner.py -v
pytest tests/test_agents.py -v
pytest tests/test_sandbox.py -v
pytest tests/test_evolution.py -v
pytest tests/ -v  # 全部测试
```

---

## 执行顺序

1. MCP Client (Task 1.1) - 基础设施
2. 工具框架 (Task 2.1) - 依赖 MCP
3. LLM 路由增强 (Task 7.1) - 支持 tools
4. 任务规划器 (Task 3.1) - 依赖工具和 LLM
5. 多 Agent 编排 (Task 4.1) - 依赖规划器
6. 代码沙箱 (Task 5.1) - 独立
7. 自进化 (Task 6.1) - 依赖其他模块
8. 集成 (Task 8.1) - 最后
