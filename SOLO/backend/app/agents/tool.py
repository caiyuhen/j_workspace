"""
工具代理

工具集成专家，提供：
- Skill发现
- Skill调用
- MCP适配
- 结果转换
"""
from typing import Dict, List, Optional
from app.agents.base import BaseAgent, TaskContext, TaskResult


class ToolAgent(BaseAgent):
    """
    工具代理 - 工具集成专家
    
    管理Skill和外部工具的调用，支持skillhub.cn和MCP双协议。
    """
    
    name = "工具代理"
    display_name = "工具代理"
    type = "tool"
    description = "工具集成专家，管理Skill和外部工具的调用"
    capabilities = [
        "skill_discovery",
        "skill_invocation",
        "mcp_adapter",
        "result_transformation"
    ]
    
    def __init__(self):
        super().__init__()
        self.skills: Dict[str, Dict] = {}
        self._setup_default_skills()
    
    def _setup_default_skills(self):
        """设置默认Skill列表"""
        self.skills = {
            "symptom_analyzer": {
                "skill_id": "symptom_analyzer",
                "name": "症状分析器",
                "description": "分析患者症状，提取关键信息",
                "category": "diagnosis",
                "protocol": "skillhub",
                "status": "active"
            },
            "drug_interaction": {
                "skill_id": "drug_interaction",
                "name": "药物相互作用检查",
                "description": "检查药物之间的相互作用",
                "category": "pharmacy",
                "protocol": "mcp",
                "status": "active"
            },
            "lab_interpretation": {
                "skill_id": "lab_interpretation",
                "name": "检验结果解读",
                "description": "解读临床检验结果",
                "category": "diagnosis",
                "protocol": "skillhub",
                "status": "active"
            },
            "imaging_analysis": {
                "skill_id": "imaging_analysis",
                "name": "影像辅助分析",
                "description": "辅助分析医学影像",
                "category": "diagnosis",
                "protocol": "skillhub",
                "status": "active"
            },
            "clinical_trial_search": {
                "skill_id": "clinical_trial_search",
                "name": "临床试验检索",
                "description": "检索相关临床试验",
                "category": "research",
                "protocol": "mcp",
                "status": "active"
            }
        }
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行工具任务"""
        task_type = context.metadata.get("task_type", "skill_invocation")
        
        handlers = {
            "skill_discovery": self._skill_discovery,
            "skill_invocation": self._skill_invocation,
            "mcp_adapter": self._mcp_adapter,
            "result_transformation": self._result_transformation
        }
        
        handler = handlers.get(task_type)
        if handler:
            return await handler(context)
        
        return TaskResult(
            task_id=context.task_id,
            success=False,
            output=None,
            error=f"Unknown task type: {task_type}"
        )
    
    async def _skill_discovery(self, context: TaskContext) -> TaskResult:
        """发现可用Skill"""
        input_data = context.input if isinstance(context.input, dict) else {}
        category = input_data.get("category")
        protocol = input_data.get("protocol")
        
        skills = list(self.skills.values())
        
        if category:
            skills = [s for s in skills if s["category"] == category]
        if protocol:
            skills = [s for s in skills if s["protocol"] == protocol]
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output={
                "skills": skills,
                "total": len(skills)
            }
        )
    
    async def _skill_invocation(self, context: TaskContext) -> TaskResult:
        """调用Skill"""
        input_data = context.input if isinstance(context.input, dict) else {}
        skill_id = input_data.get("skill_id")
        params = input_data.get("params", {})
        
        if not skill_id:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                output=None,
                error="skill_id is required"
            )
        
        skill = self.skills.get(skill_id)
        if not skill:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                output=None,
                error=f"Skill not found: {skill_id}"
            )
        
        # 根据协议调用不同的服务
        if skill["protocol"] == "skillhub":
            result = await self._invoke_skillhub(skill, params, session_id=context.conversation_id)
        elif skill["protocol"] == "mcp":
            result = await self._invoke_mcp(skill, params, session_id=context.conversation_id)
        else:
            result = await self._invoke_local(skill, params, session_id=context.conversation_id)
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output={
                "skill_id": skill_id,
                "result": result,
                "protocol": skill["protocol"]
            }
        )
    
    async def _invoke_skillhub(self, skill: Dict, params: Dict, session_id: str) -> Dict:
        """调用SkillHub Skill"""
        # TODO: 实现实际的SkillHub调用
        # 这里使用LLM模拟Skill功能
        response = await self.call_llm(
            [
                {
                    "role": "system",
                    "content": f"你是{skill['name']}工具。请处理用户的请求。"
                },
                {"role": "user", "content": str(params)}
            ],
            session_id=session_id
        )
        return response
    
    async def _invoke_mcp(self, skill: Dict, params: Dict, session_id: str) -> Dict:
        """调用MCP工具"""
        # TODO: 实现实际的MCP调用
        response = await self.call_llm(
            [
                {
                    "role": "system",
                    "content": f"你是MCP工具{skill['name']}。请处理用户的请求。"
                },
                {"role": "user", "content": str(params)}
            ],
            session_id=session_id
        )
        return response
    
    async def _invoke_local(self, skill: Dict, params: Dict, session_id: str) -> Dict:
        """调用本地工具"""
        response = await self.call_llm(
            [
                {
                    "role": "system",
                    "content": f"你是本地工具{skill['name']}。请处理用户的请求。"
                },
                {"role": "user", "content": str(params)}
            ],
            session_id=session_id
        )
        return response
    
    async def _mcp_adapter(self, context: TaskContext) -> TaskResult:
        """MCP协议适配"""
        input_data = context.input if isinstance(context.input, dict) else {}
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output={"message": "MCP适配功能", "input": input_data}
        )
    
    async def _result_transformation(self, context: TaskContext) -> TaskResult:
        """结果转换"""
        input_data = context.input if isinstance(context.input, dict) else {}
        result = input_data.get("result")
        target_format = input_data.get("target_format", "json")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": f"请将以下结果转换为{target_format}格式。"
            },
            {"role": "user", "content": str(result)}
        ], session_id=context.conversation_id)
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    def register_skill(self, skill: Dict):
        """注册新Skill"""
        self.skills[skill["skill_id"]] = skill
    
    def unregister_skill(self, skill_id: str) -> bool:
        """注销Skill"""
        if skill_id in self.skills:
            del self.skills[skill_id]
            return True
        return False
