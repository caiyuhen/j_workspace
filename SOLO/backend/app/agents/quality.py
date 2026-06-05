"""
质控代理

质量与安全守护者，提供：
- 结果审核
- 安全检查
- 合规验证
- 偏见检测
- 引用验证
"""
from typing import Dict, List
from app.agents.base import BaseAgent, TaskContext, TaskResult


class QualityAgent(BaseAgent):
    """
    质控代理 - 质量与安全守护者
    
    确保输出质量和合规性。
    """
    
    name = "质控代理"
    display_name = "质控代理"
    type = "quality"
    description = "质量与安全守护者，确保输出质量和合规性"
    capabilities = [
        "result_review",
        "safety_check",
        "compliance_verification",
        "bias_detection",
        "citation_verification"
    ]
    
    # 质量标准
    QUALITY_STANDARDS = {
        "medical_accuracy": 0.95,  # 医学准确性 ≥95%
        "relevance": 0.90,         # 响应相关性 ≥90%
        "safety_compliance": 1.0,  # 安全合规率 100%
        "user_satisfaction": 0.85  # 用户满意度 ≥85%
    }
    
    # 敏感词列表
    SENSITIVE_WORDS = [
        "绝对", "一定", "保证治愈", "根治", "无副作用"
    ]
    
    # 危险信号关键词
    DANGER_SIGNALS = [
        "胸痛", "呼吸困难", "意识障碍", "大出血", "剧烈头痛"
    ]
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行质控任务"""
        task_type = context.metadata.get("task_type", "result_review")
        
        handlers = {
            "result_review": self._result_review,
            "safety_check": self._safety_check,
            "compliance_verification": self._compliance_verification,
            "bias_detection": self._bias_detection,
            "citation_verification": self._citation_verification
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
    
    async def _result_review(self, context: TaskContext) -> TaskResult:
        """结果审核"""
        input_data = context.input if isinstance(context.input, dict) else {"content": str(context.input)}
        content = input_data.get("content", "")
        agent_name = input_data.get("agent", "unknown")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医学内容审核专家。请审核以下内容：

1. 医学准确性评估 (0-100分)
2. 内容完整性评估 (0-100分)
3. 逻辑连贯性评估 (0-100分)
4. 语言表达评估 (0-100分)
5. 总体评分
6. 改进建议
7. 是否通过审核 (pass/review/reject)

请以JSON格式返回审核报告。"""
            },
            {
                "role": "user",
                "content": f"来源代理: {agent_name}\n内容: {content}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _safety_check(self, context: TaskContext) -> TaskResult:
        """安全检查"""
        input_data = context.input if isinstance(context.input, dict) else {"content": str(context.input)}
        content = input_data.get("content", "")
        
        # 检查敏感词
        found_sensitive = [w for w in self.SENSITIVE_WORDS if w in content]
        
        # 检查危险信号
        found_danger = [w for w in self.DANGER_SIGNALS if w in content]
        
        # 使用LLM进行深度安全分析
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医学安全审核专家。请检查内容的安全性：

1. 是否包含不当医疗建议
2. 是否存在误导性信息
3. 是否遗漏重要风险提示
4. 是否符合医疗安全规范
5. 安全风险评估 (low/medium/high/critical)
6. 安全建议

请以JSON格式返回安全检查报告。"""
            },
            {"role": "user", "content": f"内容: {content}"}
        ])
        
        result = response
        result["sensitive_words_found"] = found_sensitive
        result["danger_signals_found"] = found_danger
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=result
        )
    
    async def _compliance_verification(self, context: TaskContext) -> TaskResult:
        """合规验证"""
        input_data = context.input if isinstance(context.input, dict) else {"content": str(context.input)}
        content = input_data.get("content", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医疗合规审核专家。请验证内容是否符合医疗规范：

1. 是否符合《互联网诊疗管理办法》
2. 是否符合《医疗质量管理办法》
3. 是否包含必要的免责声明
4. 是否明确说明仅供参考
5. 是否避免替代医生诊断
6. 合规性评估 (compliant/partial/non-compliant)
7. 合规建议

请以JSON格式返回合规验证报告。"""
            },
            {"role": "user", "content": f"内容: {content}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _bias_detection(self, context: TaskContext) -> TaskResult:
        """偏见检测"""
        input_data = context.input if isinstance(context.input, dict) else {"content": str(context.input)}
        content = input_data.get("content", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位AI偏见检测专家。请检测内容中可能存在的偏见：

1. 性别偏见检测
2. 年龄偏见检测
3. 种族偏见检测
4. 地域偏见检测
5. 其他潜在偏见
6. 偏见风险评估 (none/low/medium/high)
7. 修正建议

请以JSON格式返回偏见检测报告。"""
            },
            {"role": "user", "content": f"内容: {content}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _citation_verification(self, context: TaskContext) -> TaskResult:
        """引用验证"""
        input_data = context.input if isinstance(context.input, dict) else {"citations": []}
        citations = input_data.get("citations", [])
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医学文献引用审核专家。请验证引用的准确性：

1. 引用来源验证
2. 引用内容准确性
3. 引用格式规范性
4. 引用时效性
5. 引用可信度评估
6. 修正建议

请以JSON格式返回引用验证报告。"""
            },
            {"role": "user", "content": f"引用列表: {citations}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
