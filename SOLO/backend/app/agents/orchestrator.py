"""
编排代理

系统的核心大脑，负责：
- 任务解析：理解用户意图
- 任务分解：将复杂任务拆解为子任务
- 代理调度：选择合适的专业代理
- 结果整合：汇总各代理输出
"""
import logging
from typing import Dict, List, Optional
from app.agents.base import BaseAgent, TaskContext, TaskResult

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    编排代理 - 系统核心大脑
    
    负责任务的解析、分解、调度和结果整合。
    通过调用大模型服务 `/chat` 接口获取RAG增强的响应。
    """
    
    name = "编排专家"
    display_name = "编排专家"
    type = "orchestrator"
    description = "任务编排专家，负责分解任务和调度其他专家"
    capabilities = ["task_parsing", "task_decomposition", "agent_scheduling", "result_aggregation"]
    
    def __init__(self):
        super().__init__()
        self.agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent):
        """
        注册代理
        
        Args:
            agent: 要注册的代理实例
        """
        self.agents[agent.name] = agent
    
    def unregister_agent(self, agent_name: str):
        """注销代理"""
        if agent_name in self.agents:
            del self.agents[agent_name]
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        执行编排任务
        
        流程：
        1. 解析用户意图
        2. 分解任务
        3. 调度代理执行
        4. 整合结果
        """
        try:
            # Step 1: 解析意图
            intent = await self._parse_intent(context.input, context)
            logger.info(f"解析意图结果: {intent}")
            
            # Step 2: 分解任务
            subtasks = await self._decompose_task(intent, context)
            logger.info(f"分解任务结果: {subtasks}")
            
            # Step 3: 调度执行
            results = await self._execute_subtasks(subtasks, context)
            logger.info(f"执行结果数量: {len(results)}, 成功: {sum(1 for r in results if r.success)}")
            
            # Step 4: 整合结果
            final_result = await self._aggregate_results(results, context)
            logger.info(f"最终结果: {final_result}")
            
            return TaskResult(
                task_id=context.task_id,
                success=True,
                output=final_result
            )
            
        except Exception as e:
            logger.error(f"编排执行失败: {e}")
            return TaskResult(
                task_id=context.task_id,
                success=False,
                output=None,
                error=str(e)
            )
    
    async def _parse_intent(self, user_input: str, context: TaskContext) -> Dict:
        """
        解析用户意图
        
        使用大模型分析用户输入，识别意图和关键实体。
        大模型服务会自动进行RAG检索增强。
        """
        try:
            response = await self.call_llm(
                [
                    {
                        "role": "system",
                        "content": """你是一个医学意图识别专家。分析用户输入，识别以下信息：
1. intent_type: 意图类型(diagnosis/research/consultation/knowledge)
2. entities: 关键实体列表
3. confidence: 置信度(0-1)
4. task_complexity: 任务复杂度(simple/medium/complex)

请以JSON格式返回结果。"""
                    },
                    {"role": "user", "content": f"分析以下医学输入：\n{user_input}"}
                ],
                session_id=context.conversation_id
            )
            
            # 处理响应
            if isinstance(response, dict):
                # 如果响应包含 content 字段，提取内容
                if "content" in response:
                    content = response["content"]
                    # 尝试解析 JSON
                    try:
                        import json
                        # 查找 JSON 块
                        if "```json" in content:
                            json_str = content.split("```json")[1].split("```")[0].strip()
                            return json.loads(json_str)
                        elif "{" in content and "}" in content:
                            json_str = content[content.find("{"):content.rfind("}")+1]
                            return json.loads(json_str)
                    except:
                        pass
                # 直接返回响应
                return response
            
            # 默认返回
            return {
                "intent_type": "consultation",
                "entities": [],
                "confidence": 0.5,
                "task_complexity": "simple"
            }
        except Exception as e:
            # 出错时返回默认意图
            return {
                "intent_type": "consultation",
                "entities": [],
                "confidence": 0.5,
                "task_complexity": "simple",
                "error": str(e)
            }
    
    async def _decompose_task(self, intent: Dict, context: TaskContext) -> List[Dict]:
        """
        分解任务
        
        根据意图将复杂任务分解为可执行的子任务。
        """
        try:
            # 简单任务直接返回
            if intent.get("task_complexity") == "simple":
                return [{
                    "task_id": f"{context.task_id}_0",
                    "type": intent.get("intent_type", "consultation"),
                    "input": context.input
                }]
            
            # 复杂任务需要分解
            response = await self.call_llm([
                {
                    "role": "system",
                    "content": """你是一个任务分解专家。将医学任务分解为子任务，每个子任务包含：
- task_id: 子任务ID
- type: 任务类型
- input: 输入数据
- dependencies: 依赖的任务ID列表

请以JSON数组格式返回子任务列表。"""
                },
                {"role": "user", "content": f"分解以下任务：\n意图: {intent}\n原始输入: {context.input}"}
            ], session_id=context.conversation_id)
            
            # 处理响应
            if isinstance(response, dict):
                if "subtasks" in response:
                    return response["subtasks"]
                if "content" in response:
                    content = response["content"]
                    try:
                        import json
                        if "```json" in content:
                            json_str = content.split("```json")[1].split("```")[0].strip()
                            return json.loads(json_str)
                        elif "[" in content and "]" in content:
                            json_str = content[content.find("["):content.rfind("]")+1]
                            return json.loads(json_str)
                    except:
                        pass
            
            # 默认返回简单任务
            return [{
                "task_id": f"{context.task_id}_0",
                "type": intent.get("intent_type", "consultation"),
                "input": context.input
            }]
        except Exception as e:
            logger.error(f"任务分解失败: {e}")
            return [{
                "task_id": f"{context.task_id}_0",
                "type": "consultation",
                "input": context.input
            }]
    
    async def _execute_subtasks(
        self, 
        subtasks: List[Dict], 
        context: TaskContext
    ) -> List[TaskResult]:
        """
        执行子任务
        
        根据任务类型调度合适的专业代理执行。
        """
        # 意图类型到能力的映射
        type_mapping = {
            "diagnosis": "diagnosis_suggestion",
            "consultation": "health_consultation",
            "research": "literature_search",
            "knowledge": "knowledge_query",
            "tool": "tool_execution",
            "quality": "quality_check",
            "learning": "feedback_learning"
        }
        
        results = []
        
        for subtask in subtasks:
            task_type = subtask.get("type")
            # 获取映射后的能力类型
            capability = type_mapping.get(task_type, task_type)
            
            logger.info(f"执行子任务: task_type={task_type}, capability={capability}")
            
            agent = self._find_agent_for_task(task_type)
            logger.info(f"找到代理: {agent.name if agent else 'None'}")
            
            if agent:
                subtask_context = TaskContext(
                    task_id=subtask.get("task_id", context.task_id),
                    user_id=context.user_id,
                    conversation_id=context.conversation_id,
                    input=subtask.get("input", context.input),
                    metadata={"task_type": capability}  # 使用映射后的能力类型
                )
                
                result = await agent.execute(subtask_context)
                logger.info(f"代理执行结果: success={result.success}")
                results.append(result)
            else:
                # 没有找到合适的代理，使用LLM直接处理
                logger.info("没有找到代理，使用LLM直接处理")
                result = await self._handle_with_llm(subtask, context)
                results.append(result)
        
        return results
    
    def _find_agent_for_task(self, task_type: str) -> Optional[BaseAgent]:
        """
        查找能处理指定任务类型的代理
        
        支持意图类型到代理能力的映射：
        - diagnosis -> diagnosis_suggestion
        - consultation -> health_consultation
        - research -> literature_search
        - knowledge -> knowledge_query
        """
        # 意图类型到能力的映射
        type_mapping = {
            "diagnosis": "diagnosis_suggestion",
            "consultation": "health_consultation",
            "research": "literature_search",
            "knowledge": "knowledge_query",
            "tool": "tool_execution",
            "quality": "quality_check",
            "learning": "feedback_learning"
        }
        
        # 获取实际能力类型
        capability = type_mapping.get(task_type, task_type)
        
        logger.info(f"查找代理: task_type={task_type}, capability={capability}")
        
        # 查找代理
        for name, agent in self.agents.items():
            if agent.can_handle(capability) or agent.can_handle(task_type):
                logger.info(f"找到匹配代理: {name}")
                return agent
        
        # 如果没找到，返回第一个可用的代理
        if self.agents:
            first_agent = list(self.agents.values())[0]
            logger.info(f"使用默认代理: {first_agent.name}")
            return first_agent
        
        logger.warning("没有找到任何代理")
        return None
    
    async def _handle_with_llm(
        self, 
        subtask: Dict, 
        context: TaskContext
    ) -> TaskResult:
        """使用LLM直接处理任务"""
        response = await self.call_llm(
            [
                {"role": "system", "content": "你是一个医学AI助手。"},
                {"role": "user", "content": str(subtask.get("input", context.input))}
            ],
            session_id=context.conversation_id
        )
        
        return TaskResult(
            task_id=subtask.get("task_id", context.task_id),
            success=True,
            output=response
        )
    
    async def _aggregate_results(self, results: List[TaskResult], context: TaskContext) -> Dict:
        """
        整合结果
        
        将多个代理的输出整合为最终响应。
        """
        successful_results = [r.output for r in results if r.success and r.output]
        
        if not successful_results:
            # 检查是否有错误信息
            errors = [r.error for r in results if r.error]
            if errors:
                return {"content": f"处理请求时发生错误：{errors[0]}"}
            return {"content": "抱歉，无法处理您的请求，请稍后重试。"}
        
        # 单个结果直接返回
        if len(successful_results) == 1:
            result = successful_results[0]
            # 确保结果有 content 字段
            if isinstance(result, dict):
                if "content" in result:
                    return result
                elif "response" in result:
                    return {"content": result["response"], "sources": result.get("retrieved_knowledge", [])}
                else:
                    return {"content": str(result)}
            return {"content": str(result)}
        
        # 多个结果需要整合
        response = await self.call_llm(
            [
                {
                    "role": "system",
                    "content": "你是一个结果整合专家。将多个医学分析结果整合为一个完整、连贯的响应。"
                },
                {"role": "user", "content": f"整合以下结果：\n{successful_results}"}
            ],
            session_id=context.conversation_id
        )
        
        # 确保响应格式正确
        if isinstance(response, dict):
            if "content" in response:
                return response
            elif "response" in response:
                return {"content": response["response"]}
        
        return {"content": str(response)}
