"""
知识代理

医学知识查询专家，提供：
- 知识查询
- 术语解释
- 药物查询
- 疾病百科
- 指南检索
"""
from typing import Dict, List
from app.agents.base import BaseAgent, TaskContext, TaskResult


class KnowledgeAgent(BaseAgent):
    """
    知识代理 - 医学知识查询专家
    
    通过调用大模型服务(192.168.0.214:8802/chat/)获取RAG增强的知识查询。
    大模型内置的RAG会自动检索医学知识库。
    """
    
    name = "知识代理"
    display_name = "知识代理"
    type = "knowledge"
    description = "医学知识查询专家，管理医学知识图谱和术语库"
    capabilities = [
        "knowledge_query",
        "term_explanation",
        "drug_query",
        "disease_encyclopedia",
        "guideline_search"
    ]
    
    # RAG内置知识库范围
    BUILTIN_KNOWLEDGE_BASES = [
        "疾病知识库 (ICD-10/ICD-11编码、疾病百科、诊断标准)",
        "药物知识库 (DrugBank药品信息、药物相互作用、用药指南)",
        "临床指南库 (诊疗指南、专家共识、临床路径)",
        "医学文献库 (论文摘要、研究数据)",
        "术语词典 (SNOMED CT医学术语、医学词典)"
    ]
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """执行知识查询任务"""
        task_type = context.metadata.get("task_type", "knowledge_query")
        
        handlers = {
            "knowledge_query": self._knowledge_query,
            "term_explanation": self._term_explanation,
            "drug_query": self._drug_query,
            "disease_encyclopedia": self._disease_encyclopedia,
            "guideline_search": self._guideline_search
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
    
    async def _knowledge_query(self, context: TaskContext) -> TaskResult:
        """
        知识查询
        
        通过大模型内置RAG检索医学知识库。
        """
        input_data = context.input if isinstance(context.input, dict) else {"query": str(context.input)}
        query = input_data.get("query", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": f"""你是一位医学知识专家。请查询相关知识并回答：

内置知识库范围：
{chr(10).join(self.BUILTIN_KNOWLEDGE_BASES)}

请提供：
1. 知识内容
2. 知识来源（如ICD编码、指南名称等）
3. 相关知识链接
4. 参考文献建议

请以JSON格式返回知识查询结果。"""
            },
            {"role": "user", "content": f"查询: {query}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _term_explanation(self, context: TaskContext) -> TaskResult:
        """术语解释"""
        input_data = context.input if isinstance(context.input, dict) else {"term": str(context.input)}
        term = input_data.get("term", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位医学术语专家。请解释医学术语：

1. 术语定义
2. 英文名称
3. 相关概念
4. 临床意义
5. 常见用法示例

请以JSON格式返回术语解释。"""
            },
            {"role": "user", "content": f"术语: {term}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _drug_query(self, context: TaskContext) -> TaskResult:
        """药物查询"""
        input_data = context.input if isinstance(context.input, dict) else {"drug": str(context.input)}
        drug = input_data.get("drug", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位药物信息专家。请提供药物详细信息：

1. 药物基本信息
   - 通用名/商品名
   - 药物分类
   - 剂型规格
2. 药理作用
3. 适应症
4. 用法用量
5. 不良反应
6. 禁忌症
7. 药物相互作用
8. 特殊人群用药
9. 储存条件

请以JSON格式返回药物信息。"""
            },
            {"role": "user", "content": f"药物: {drug}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _disease_encyclopedia(self, context: TaskContext) -> TaskResult:
        """疾病百科"""
        input_data = context.input if isinstance(context.input, dict) else {"disease": str(context.input)}
        disease = input_data.get("disease", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位疾病知识专家。请提供疾病详细信息：

1. 疾病概述
   - 疾病名称
   - ICD编码
   - 英文名称
2. 病因
3. 流行病学
4. 临床表现
5. 诊断标准
6. 鉴别诊断
7. 治疗方案
8. 预后
9. 预防措施

请以JSON格式返回疾病百科。"""
            },
            {"role": "user", "content": f"疾病: {disease}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _guideline_search(self, context: TaskContext) -> TaskResult:
        """指南检索"""
        input_data = context.input if isinstance(context.input, dict) else {"keyword": str(context.input)}
        keyword = input_data.get("keyword", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位临床指南专家。请检索相关临床指南：

1. 相关指南列表
   - 指南名称
   - 发布机构
   - 发布年份
2. 指南要点
3. 推荐意见
4. 证据等级
5. 更新情况

请以JSON格式返回指南检索结果。"""
            },
            {"role": "user", "content": f"关键词: {keyword}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
