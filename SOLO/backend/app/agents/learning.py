"""
学习代理

系统进化引擎，提供：
- 反馈学习
- 知识更新
- 效果评估
- 趋势分析
"""
from typing import Dict, List
from app.agents.base import BaseAgent, TaskContext, TaskResult


class LearningAgent(BaseAgent):
    """
    学习代理 - 系统进化引擎
    
    持续学习和优化系统能力。
    """
    
    name = "学习代理"
    display_name = "学习代理"
    type = "learning"
    description = "系统进化引擎，持续学习和优化系统能力"
    capabilities = [
        "feedback_learning",
        "knowledge_update",
        "effect_evaluation",
        "trend_analysis"
    ]
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行学习任务"""
        task_type = context.metadata.get("task_type", "feedback_learning")
        
        handlers = {
            "feedback_learning": self._feedback_learning,
            "knowledge_update": self._knowledge_update,
            "effect_evaluation": self._effect_evaluation,
            "trend_analysis": self._trend_analysis
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
    
    async def _feedback_learning(self, context: TaskContext) -> TaskResult:
        """反馈学习"""
        input_data = context.input if isinstance(context.input, dict) else {}
        feedback_type = input_data.get("type", "general")
        content = input_data.get("content", "")
        rating = input_data.get("rating")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位AI学习优化专家。请分析用户反馈并提取学习信息：

1. 反馈类型分析
2. 用户满意度评估
3. 问题识别
4. 改进建议
5. 学习要点
6. 优先级评估

请以JSON格式返回学习分析报告。"""
            },
            {
                "role": "user",
                "content": f"反馈类型: {feedback_type}\n反馈内容: {content}\n评分: {rating}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _knowledge_update(self, context: TaskContext) -> TaskResult:
        """知识更新"""
        input_data = context.input if isinstance(context.input, dict) else {}
        update_type = input_data.get("update_type", "add")
        knowledge = input_data.get("knowledge", {})
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位知识管理专家。请处理知识更新请求：

1. 知识验证
2. 与现有知识的关系
3. 更新影响评估
4. 更新建议
5. 版本管理建议

请以JSON格式返回知识更新报告。"""
            },
            {
                "role": "user",
                "content": f"更新类型: {update_type}\n知识内容: {knowledge}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _effect_evaluation(self, context: TaskContext) -> TaskResult:
        """效果评估"""
        input_data = context.input if isinstance(context.input, dict) else {}
        period = input_data.get("period", "daily")
        metrics = input_data.get("metrics", {})
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位系统效果评估专家。请评估系统整体效果：

1. 关键指标分析
   - 任务完成率
   - 响应时间
   - 用户满意度
   - 错误率
2. 趋势分析
3. 问题识别
4. 改进建议
5. 目标达成评估

请以JSON格式返回效果评估报告。"""
            },
            {
                "role": "user",
                "content": f"评估周期: {period}\n指标数据: {metrics}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _trend_analysis(self, context: TaskContext) -> TaskResult:
        """趋势分析"""
        input_data = context.input if isinstance(context.input, dict) else {}
        data_type = input_data.get("data_type", "usage")
        time_range = input_data.get("time_range", "7d")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位数据分析专家。请分析使用趋势：

1. 数据概览
2. 趋势识别
3. 异常检测
4. 预测分析
5. 行动建议

请以JSON格式返回趋势分析报告。"""
            },
            {
                "role": "user",
                "content": f"数据类型: {data_type}\n时间范围: {time_range}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
