"""
咨询代理

健康咨询顾问，提供：
- 健康咨询
- 症状自查
- 就医指导
- 用药指导
- 健康教育
"""
from typing import Dict
from app.agents.base import BaseAgent, TaskContext, TaskResult


class ConsultationAgent(BaseAgent):
    """
    咨询代理 - 健康咨询顾问
    
    面向患者和公众提供健康咨询服务。
    通过调用大模型服务(192.168.0.214:8802/chat/)获取RAG增强的响应。
    """
    
    name = "咨询代理"
    display_name = "咨询代理"
    type = "consultation"
    description = "健康咨询顾问，面向患者和公众提供健康指导"
    capabilities = [
        "health_consultation",
        "symptom_check",
        "medical_guidance",
        "medication_guidance",
        "health_education"
    ]
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行咨询任务"""
        task_type = context.metadata.get("task_type", "health_consultation")
        
        handlers = {
            "health_consultation": self._health_consultation,
            "symptom_check": self._symptom_check,
            "medical_guidance": self._medical_guidance,
            "medication_guidance": self._medication_guidance,
            "health_education": self._health_education
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
    
    async def _health_consultation(self, context: TaskContext) -> TaskResult:
        """健康咨询"""
        input_data = context.input if isinstance(context.input, dict) else {"question": str(context.input)}
        question = input_data.get("question", "")
        user_info = input_data.get("user_info", {})
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位友善的健康咨询顾问。请用通俗易懂的语言回答用户的健康问题：

1. 问题解答
2. 相关健康建议
3. 注意事项
4. 何时需要就医

注意：
- 使用亲切、易懂的语言
- 不要给出明确诊断
- 提醒用户必要时就医
- 不要替代医生的专业建议

请以JSON格式返回回答。"""
            },
            {
                "role": "user",
                "content": f"用户问题: {question}\n用户信息: {user_info}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _symptom_check(self, context: TaskContext) -> TaskResult:
        """症状自查"""
        input_data = context.input if isinstance(context.input, dict) else {"symptoms": str(context.input)}
        symptoms = input_data.get("symptoms", [])
        duration = input_data.get("duration", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位健康咨询顾问，帮助用户进行症状自查。请提供：

1. 症状分析
2. 可能的原因（注意：仅供参考，不是诊断）
3. 自我护理建议
4. 危险信号（需要立即就医的情况）
5. 建议就诊科室
6. 紧急程度评估

重要提醒：
- 明确说明这只是初步分析，不能替代医生诊断
- 如有严重症状，建议立即就医

请以JSON格式返回自查报告。"""
            },
            {
                "role": "user",
                "content": f"症状: {symptoms}\n持续时间: {duration}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _medical_guidance(self, context: TaskContext) -> TaskResult:
        """就医指导"""
        input_data = context.input if isinstance(context.input, dict) else {"condition": str(context.input)}
        condition = input_data.get("condition", "")
        symptoms = input_data.get("symptoms", [])
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位就医指导顾问。请提供就医建议：

1. 建议就诊科室
2. 就诊前准备
3. 可能需要的检查
4. 就诊时需要告诉医生的信息
5. 就诊时机建议（是否需要急诊）

请以JSON格式返回就医指导。"""
            },
            {
                "role": "user",
                "content": f"情况: {condition}\n症状: {symptoms}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _medication_guidance(self, context: TaskContext) -> TaskResult:
        """用药指导"""
        input_data = context.input if isinstance(context.input, dict) else {"medication": str(context.input)}
        medication = input_data.get("medication", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位用药指导顾问。请提供用药信息：

1. 药物基本信息
2. 适应症
3. 用法用量
4. 注意事项
5. 可能的副作用
6. 药物相互作用
7. 特殊人群用药注意

重要提醒：
- 用药前请仔细阅读说明书
- 遵医嘱用药
- 如有不良反应，请及时就医

请以JSON格式返回用药指导。"""
            },
            {"role": "user", "content": f"药物: {medication}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _health_education(self, context: TaskContext) -> TaskResult:
        """健康教育"""
        input_data = context.input if isinstance(context.input, dict) else {"topic": str(context.input)}
        topic = input_data.get("topic", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位健康教育专家。请提供健康科普内容：

1. 主题概述
2. 关键知识点
3. 预防措施
4. 健康建议
5. 常见误区

要求：
- 使用通俗易懂的语言
- 内容科学准确
- 提供实用建议

请以JSON格式返回科普内容。"""
            },
            {"role": "user", "content": f"科普主题: {topic}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
