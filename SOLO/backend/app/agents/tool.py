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
from app.services.skill_registry import skill_registry


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
        "tool_execution",
        "mcp_adapter",
        "result_transformation"
    ]
    
    def __init__(self):
        super().__init__()
        self.skills: Dict[str, Dict] = {}
        self._setup_default_skills()
    
    def _setup_default_skills(self):
        """设置默认Skill列表"""
        # ToolAgent 的默认 Skill 列表与 Skills API 共享同一来源（skill_registry）
        # 这里保留一个“常用技能”索引，skill_id 直接使用 Skills API 的 id
        self.skills = {
            "skill_symptom_checker": {"skill_id": "skill_symptom_checker", "name": "症状自查"},
            "skill_lab_interpretation": {"skill_id": "skill_lab_interpretation", "name": "检验结果解读"},
            "skill_medical_diagnosis": {"skill_id": "skill_medical_diagnosis", "name": "医学诊断"},
            "skill_drug_interaction": {"skill_id": "skill_drug_interaction", "name": "药物相互作用检查"},
            "skill_dosage_calculator": {"skill_id": "skill_dosage_calculator", "name": "用药剂量计算"},
            "skill_literature_search": {"skill_id": "skill_literature_search", "name": "医学文献检索"},
            "skill_clinical_guideline": {"skill_id": "skill_clinical_guideline", "name": "临床指南查询"},
            "skill_image_analysis": {"skill_id": "skill_image_analysis", "name": "医学影像分析"},
        }
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行工具任务"""
        task_type = context.metadata.get("task_type", "skill_invocation")
        
        handlers = {
            "skill_discovery": self._skill_discovery,
            "skill_invocation": self._skill_invocation,
            "tool_execution": self._skill_invocation,
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

        skills = skill_registry.list_skills(category=category, protocol=protocol)
        
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
        config = input_data.get("config")
        
        if not skill_id:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                output=None,
                error="skill_id is required"
            )

        result = await skill_registry.execute_skill(
            skill_id=skill_id,
            input_data=params,
            config=config,
            user_id=context.user_id,
            conversation_id=context.conversation_id
        )

        return TaskResult(
            task_id=context.task_id,
            success=True,
            output={
                "skill_id": skill_id,
                "result": result,
                "protocol": (skill_registry.get_skill(skill_id) or {}).get("protocol")
            }
        )
    
    # 协议执行已统一交给 skill_registry（Skills API 与 ToolAgent 共用）
    
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
