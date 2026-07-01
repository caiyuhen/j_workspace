"""
Skill 数据模型
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class StepType(str, Enum):
    """步骤类型"""
    LLM_CALL = "llm_call"           # 调用 LLM
    TOOL_CALL = "tool_call"         # 调用工具
    AGENT_CALL = "agent_call"       # 调用其他 Agent
    CONDITION = "condition"         # 条件分支
    LOOP = "loop"                   # 循环
    SKILL_CALL = "skill_call"       # 调用其他 Skill
    USER_INPUT = "user_input"       # 等待用户输入
    OUTPUT = "output"               # 输出结果


class SkillParameter(BaseModel):
    """Skill 参数定义"""
    name: str
    description: str
    type: str = "string"            # string, number, boolean, array, object
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


class SkillStep(BaseModel):
    """Skill 执行步骤"""
    id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    step_type: StepType
    
    # 根据 step_type 的不同，使用不同的配置
    config: Dict[str, Any] = Field(default_factory=dict)
    # 例如:
    # llm_call: {prompt_template, system_prompt, model}
    # tool_call: {tool_name, arguments_mapping}
    # condition: {condition_expression, true_branch, false_branch}
    # loop: {loop_condition, max_iterations, body_steps}
    # skill_call: {skill_name, arguments_mapping}
    
    # 输出变量名，后续步骤可通过 ${output_var} 引用
    output_var: Optional[str] = None
    
    # 执行条件，为空则始终执行
    condition: Optional[str] = None
    
    # 重试配置
    retry_count: int = 0
    retry_delay: float = 1.0
    
    # 错误处理: continue | stop | fallback_step_id
    on_error: str = "stop"
    fallback_step_id: Optional[str] = None


class Skill(BaseModel):
    """Skill 定义"""
    id: str = Field(default_factory=lambda: f"skill_{uuid.uuid4().hex[:8]}")
    name: str
    description: str
    version: str = "1.0.0"
    
    # 参数定义
    parameters: List[SkillParameter] = Field(default_factory=list)
    
    # 执行步骤
    steps: List[SkillStep] = Field(default_factory=list)
    
    # 元数据
    tags: List[str] = Field(default_factory=list)
    author: str = "system"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 使用统计
    usage_count: int = 0
    success_rate: float = 1.0
    
    # 是否是系统预置 Skill
    is_builtin: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def validate_parameters(self, arguments: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证输入参数"""
        errors = []
        
        for param in self.parameters:
            if param.required and param.name not in arguments:
                errors.append(f"缺少必需参数: {param.name}")
                continue
            
            value = arguments.get(param.name, param.default)
            if value is None and param.required:
                errors.append(f"参数 {param.name} 不能为 None")
                continue
            
            if param.enum and value is not None and value not in param.enum:
                errors.append(f"参数 {param.name} 的值必须在 {param.enum} 中")
        
        return len(errors) == 0, errors
    
    def get_step_by_id(self, step_id: str) -> Optional[SkillStep]:
        """根据 ID 获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def to_openai_function(self) -> Dict[str, Any]:
        """转换为 OpenAI Function Calling 格式"""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class SkillExecutionResult(BaseModel):
    """Skill 执行结果"""
    skill_id: str
    skill_name: str
    success: bool
    
    # 每个步骤的结果
    step_results: Dict[str, Any] = Field(default_factory=dict)
    
    # 最终输出
    output: Any = None
    
    # 变量上下文
    variables: Dict[str, Any] = Field(default_factory=dict)
    
    # 错误信息
    error: Optional[str] = None
    failed_step_id: Optional[str] = None
    
    # 执行统计
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0
