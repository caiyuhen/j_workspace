"""
研究代理

医学研究助手，提供：
- 文献检索
- 文献摘要
- 数据分析
- 论文辅助
- 趋势分析
"""
from typing import Dict, List
from app.agents.base import BaseAgent, TaskContext, TaskResult


class ResearchAgent(BaseAgent):
    """
    研究代理 - 医学研究助手
    
    通过调用大模型服务(192.168.0.214:8802/chat/)获取RAG增强的研究支持。
    大模型内置的RAG会自动检索相关医学文献和知识。
    """
    
    name = "研究代理"
    display_name = "研究代理"
    type = "research"
    description = "医学研究助手，支持文献检索、数据分析、论文辅助"
    capabilities = [
        "literature_search",
        "literature_summary",
        "data_analysis",
        "paper_assistance",
        "trend_analysis"
    ]
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行研究任务"""
        task_type = context.metadata.get("task_type", "literature_search")
        
        handlers = {
            "literature_search": self._literature_search,
            "literature_summary": self._literature_summary,
            "data_analysis": self._data_analysis,
            "paper_assistance": self._paper_assistance,
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
    
    async def _literature_search(self, context: TaskContext) -> TaskResult:
        """
        文献检索
        
        大模型RAG会自动检索相关医学文献。
        """
        input_data = context.input if isinstance(context.input, dict) else {"query": str(context.input)}
        query = input_data.get("query", "")
        filters = input_data.get("filters", {})
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医学文献检索专家。请根据用户查询，提供相关文献信息：

1. 检索关键词建议
2. 相关文献列表（包含：标题、作者、期刊、年份、摘要）
3. 文献相关性评分
4. 推荐阅读顺序

请以JSON格式返回结果。"""
            },
            {
                "role": "user",
                "content": f"检索主题: {query}\n筛选条件: {filters}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _literature_summary(self, context: TaskContext) -> TaskResult:
        """文献摘要生成"""
        input_data = context.input if isinstance(context.input, dict) else {"content": str(context.input)}
        content = input_data.get("content", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医学文献分析专家。请生成文献摘要：

1. 研究背景
2. 研究目的
3. 研究方法
4. 主要发现
5. 结论
6. 临床意义
7. 研究局限性

请以JSON格式返回结构化摘要。"""
            },
            {"role": "user", "content": f"文献内容:\n{content}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _data_analysis(self, context: TaskContext) -> TaskResult:
        """数据分析"""
        input_data = context.input if isinstance(context.input, dict) else {"data": str(context.input)}
        data = input_data.get("data", "")
        analysis_type = input_data.get("analysis_type", "descriptive")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医学数据分析专家。请分析提供的数据：

1. 数据描述性统计
2. 数据质量评估
3. 统计分析方法建议
4. 主要发现
5. 可视化建议
6. 结果解读

请以JSON格式返回分析报告。"""
            },
            {
                "role": "user",
                "content": f"数据:\n{data}\n分析类型: {analysis_type}"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _paper_assistance(self, context: TaskContext) -> TaskResult:
        """论文写作辅助"""
        input_data = context.input if isinstance(context.input, dict) else {"topic": str(context.input)}
        topic = input_data.get("topic", "")
        section = input_data.get("section", "introduction")
        
        section_prompts = {
            "introduction": "撰写引言部分：研究背景、研究意义、研究目的",
            "methods": "撰写方法部分：研究设计、研究对象、干预措施、测量指标、统计分析",
            "results": "撰写结果部分：基线特征、主要结果、次要结果",
            "discussion": "撰写讨论部分：主要发现解释、与既往研究比较、临床意义、局限性",
            "conclusion": "撰写结论部分：主要结论、未来研究方向"
        }
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": f"你是一位医学论文写作专家。请协助{section_prompts.get(section, '撰写论文')}。"
            },
            {"role": "user", "content": f"论文主题: {topic}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _trend_analysis(self, context: TaskContext) -> TaskResult:
        """研究趋势分析"""
        input_data = context.input if isinstance(context.input, dict) else {"field": str(context.input)}
        field = input_data.get("field", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医学研究趋势分析专家。请分析研究领域的趋势：

1. 研究热点
2. 新兴方向
3. 研究空白
4. 未来发展趋势
5. 建议关注的研究团队

请以JSON格式返回趋势分析报告。"""
            },
            {"role": "user", "content": f"研究领域: {field}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
