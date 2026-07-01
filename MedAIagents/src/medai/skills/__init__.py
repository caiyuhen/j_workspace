"""
Skill（技能）系统

Skills 是预定义的可复用工作流/任务模板，Agent 可以学习、调用和执行。
例如：肺癌诊疗流程、Meta分析写作、基金申请书撰写等。
"""

from .models import Skill, SkillStep, SkillParameter, SkillExecutionResult
from .registry import SkillRegistry
from .executor import SkillExecutor
from .learner import SkillLearner
from .builtin import register_builtin_skills

__all__ = [
    "Skill",
    "SkillStep",
    "SkillParameter",
    "SkillExecutionResult",
    "SkillRegistry",
    "SkillExecutor",
    "SkillLearner",
    "register_builtin_skills",
]
