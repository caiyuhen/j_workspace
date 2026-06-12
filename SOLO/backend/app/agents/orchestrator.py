"""
编排代理

系统的核心大脑，负责：
- 任务解析：理解用户意图
- 任务分解：将复杂任务拆解为子任务
- 代理调度：选择合适的专业代理
- 结果整合：汇总各代理输出
"""
import logging
from typing import Dict, List, Optional, Any
from app.agents.base import BaseAgent, TaskContext, TaskResult
import re

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

    def _get_quality_agent(self) -> Optional[BaseAgent]:
        for a in self.agents.values():
            if getattr(a, "type", "") == "quality":
                return a
        return None

    @staticmethod
    def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            if "{" in text and "}" in text:
                json_str = text[text.find("{"): text.rfind("}") + 1]
                return json.loads(json_str)
        except Exception:
            return None
        return None

    async def _quality_gate(
        self,
        content: str,
        context: TaskContext,
        source: str
    ) -> Dict[str, Any]:
        """
        强制质控门禁：
        - 先执行 safety_check
        - 再执行 compliance_verification
        - 高风险/不合规 => 拦截或改写为更安全版本
        """
        quality_agent = self._get_quality_agent()
        if not quality_agent:
            return {"action": "pass", "content": content}

        # 快速红旗词兜底：出现高危信号，直接加强就医提示（不依赖模型解析）
        danger_signals = ["胸痛", "呼吸困难", "意识障碍", "大出血", "剧烈头痛"]
        if any(w in (content or "") for w in danger_signals) or any(w in (str(context.input) or "") for w in danger_signals):
            blocked = (
                "检测到可能的高危症状/危险信号。以下内容仅供参考，无法替代医生诊断。\n\n"
                "建议：如出现胸痛、呼吸困难、意识改变、明显出血、剧烈头痛等情况，请立即就近急诊或拨打急救电话。\n\n"
                f"原始建议（已降级展示）：\n{content}"
            )
            return {"action": "block", "content": blocked}

        # 1) safety_check
        safety_ctx = TaskContext(
            task_id=f"{context.task_id}_quality_safety",
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            input={"content": content, "agent": source},
            metadata={"task_type": "safety_check"},
        )
        safety_res = await quality_agent.execute(safety_ctx)
        safety_json = None
        if safety_res and safety_res.output and isinstance(safety_res.output, dict):
            safety_json = self._extract_json_from_text(safety_res.output.get("content", ""))

        risk = (safety_json or {}).get("安全风险评估") or (safety_json or {}).get("safety_risk") or (safety_json or {}).get("risk") or ""
        risk = str(risk).lower()

        # 2) compliance_verification
        comp_ctx = TaskContext(
            task_id=f"{context.task_id}_quality_compliance",
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            input={"content": content},
            metadata={"task_type": "compliance_verification"},
        )
        comp_res = await quality_agent.execute(comp_ctx)
        comp_json = None
        if comp_res and comp_res.output and isinstance(comp_res.output, dict):
            comp_json = self._extract_json_from_text(comp_res.output.get("content", ""))

        compliance = (comp_json or {}).get("合规性评估") or (comp_json or {}).get("compliance") or ""
        compliance = str(compliance).lower()

        # 规则判定：高风险/不合规 => 改写或拦截
        if risk in {"high", "critical"} or "non" in compliance or "不合规" in str(comp_json):
            # 改写为更安全合规的版本（明确免责声明、避免确定性诊断/处方剂量）
            rewritten = await self.call_llm(
                [
                    {
                        "role": "system",
                        "content": (
                            "你是医疗安全与合规改写器。将用户看到的内容改写为更安全合规的医学建议，必须满足：\n"
                            "1. 不给出确定性诊断；用“可能/建议进一步检查/需医生评估”等表述\n"
                            "2. 不提供处方级别的具体用药剂量（mg/片数/频次），仅给出一般性用药注意事项并要求遵医嘱\n"
                            "3. 必须包含“仅供参考，不能替代医生诊断”的免责声明\n"
                            "4. 如可能存在紧急情况，要提示立即就医\n"
                            "只输出改写后的正文。"
                        ),
                    },
                    {"role": "user", "content": content},
                ],
                session_id=context.conversation_id,
            )
            return {"action": "rewrite", "content": rewritten.get("content", content)}

        return {"action": "pass", "content": content}

    @staticmethod
    def _parse_lab_report(text: str) -> List[Dict[str, Any]]:
        """
        将“自然语言化验单”尽量解析成结构化 lab_results。
        解析策略：
        - 按行/分隔符拆分
        - 行内提取：name + value + unit + ref_range(可选)
        """
        if not text:
            return []
        # 常见分隔符
        lines = re.split(r"[\n;；]+", text)
        results: List[Dict[str, Any]] = []

        # 示例：ALT 80 U/L (0-40) / 谷丙转氨酶: 80 U/L 参考(0-40)
        pattern = re.compile(
            r"^\s*(?P<name>[^0-9:：]+?)\s*[:：]?\s*(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-zμ/%uU\u4e00-\u9fff]+)?\s*(?P<ref>(?:\(|（)?\s*(?:参考|ref)?\s*[:：]?\s*[\d\.\-~～—–至]+\s*.*?(?:\)|）)?)?\s*$"
        )

        for raw in lines:
            s = raw.strip()
            if not s:
                continue
            m = pattern.match(s)
            if not m:
                continue
            name = (m.group("name") or "").strip()
            if len(name) < 1:
                continue
            value = float(m.group("value"))
            unit = (m.group("unit") or "").strip()
            ref = (m.group("ref") or "").strip()
            # 清理 ref 外层括号
            ref = ref.strip()
            if ref.startswith(("(", "（")) and ref.endswith((")", "）")):
                ref = ref[1:-1].strip()

            results.append(
                {
                    "name": name,
                    "value": value,
                    "unit": unit,
                    "ref_range": ref,
                }
            )

        return results
    
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
            # 兼容 task API 等场景：context.input 可能是 dict，这里统一提取可解析的文本
            raw_input: Any = context.input
            if isinstance(raw_input, dict):
                user_text = str(raw_input.get("text") or raw_input.get("message") or raw_input.get("prompt") or raw_input)
            else:
                user_text = str(raw_input)

            # Step 1: 解析意图
            intent = await self._parse_intent(user_text, context)
            logger.info(f"解析意图结果: {intent}")
            
            # Step 2: 分解任务
            # 分解阶段优先使用文本输入，避免把 dict 直接塞给各代理
            original_input = context.input
            context.input = user_text
            subtasks = await self._decompose_task(intent, context)
            context.input = original_input
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
            # 规则优先：对“明显是工具/技能调用”的输入进行稳定识别
            ruled = self._rule_based_tool_intent(user_input)
            if ruled:
                return ruled

            response = await self.call_llm(
                [
                    {
                        "role": "system",
                    "content": """你是一个医学意图识别专家。分析用户输入，识别以下信息：
1. intent_type: 意图类型(diagnosis/research/consultation/knowledge/tool/quality/learning)
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
            # 工具类任务：生成结构化 tool 子任务（供 ToolAgent 稳定执行）
            if intent.get("intent_type") == "tool":
                tool = intent.get("tool") or {}
                skill_id = tool.get("skill_id")
                params = tool.get("params") or {"text": context.input}
                config = tool.get("config")

                if not skill_id:
                    # 没指定技能时，让 tool agent 做 discovery 或直接 fallback
                    return [{
                        "task_id": f"{context.task_id}_0",
                        "type": "tool",
                        "input": {
                            "skill_id": "skill_lab_interpretation",
                            "params": {"text": context.input},
                            "config": config or {}
                        }
                    }]

                return [{
                    "task_id": f"{context.task_id}_0",
                    "type": "tool",
                    "input": {
                        "skill_id": skill_id,
                        "params": params,
                        "config": config or {}
                    }
                }]

            # 简单任务直接返回
            if intent.get("task_complexity") == "simple":
                return [{
                    "task_id": f"{context.task_id}_0",
                    "type": intent.get("intent_type", "consultation"),
                    "input": context.input
                }]
            
            # 复杂任务需要分解
            # 将可用技能列表提供给模型，减少“编造 skill_id”的情况
            try:
                from app.services.skill_registry import skill_registry
                available_skills = [
                    {
                        "id": s.get("id"),
                        "name": s.get("name"),
                        "display_name": s.get("display_name"),
                        "category": s.get("category"),
                        "protocol": s.get("protocol"),
                    }
                    for s in skill_registry.list_skills(is_active=True)
                ]
            except Exception:
                available_skills = []

            response = await self.call_llm(
                [
                    {
                        "role": "system",
                        "content": """你是一个任务分解专家。将医学任务分解为子任务，每个子任务必须满足下面 JSON Schema（数组）：

[
  {
    "task_id": "string",
    "type": "diagnosis|consultation|research|knowledge|tool|quality|learning",
    "input": "string | object",
    "dependencies": ["string"] (可选)
  }
]

当你选择 type=tool 时，input 必须是对象，格式为：
{
  "skill_id": "string (必须来自可用技能列表的 id 字段)",
  "params": { ... } (传给技能的入参),
  "config": { ... } (可选)
}

只输出 JSON，不要输出解释文字。"""
                    },
                    {
                        "role": "user",
                        "content": f"分解以下任务：\n意图: {intent}\n原始输入: {context.input}\n\n可用技能列表: {available_skills}"
                    }
                ],
                session_id=context.conversation_id
            )
            
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
    
    @staticmethod
    def _normalize_tool_result(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将 ToolAgent 的返回稳定转换为 {content, ...} 结构：
        ToolAgent.output: { skill_id, result: {success, result, error, ...}, protocol }
        """
        if not isinstance(result, dict):
            return None

        if "skill_id" in result and "result" in result and isinstance(result["result"], dict):
            exec_res = result["result"]
            if not exec_res.get("success", True):
                return {
                    "content": f"技能执行失败：{exec_res.get('error', '未知错误')}",
                    "skill_id": result.get("skill_id"),
                    "execution_id": exec_res.get("execution_id"),
                }

            payload = exec_res.get("result")
            if isinstance(payload, dict):
                if "output" in payload and isinstance(payload["output"], str):
                    content = payload["output"]
                elif "message" in payload and isinstance(payload["message"], str):
                    content = payload["message"]
                else:
                    content = str(payload)
            else:
                content = str(payload)

            return {
                "content": content,
                "skill_id": result.get("skill_id"),
                "execution_id": exec_res.get("execution_id"),
                "raw_result": payload,
            }

        return None

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
                tool_norm = self._normalize_tool_result(result)
                if tool_norm:
                    # 对关键 medical_api 工具结果强制质控门禁
                    if tool_norm.get("skill_id") in {
                        "skill_medical_api_triage",
                        "skill_medical_api_clinical",
                        "skill_medical_api_management_plan"
                    }:
                        gated = await self._quality_gate(
                            content=tool_norm.get("content", ""),
                            context=context,
                            source=f"tool:{tool_norm.get('skill_id')}",
                        )
                        tool_norm["content"] = gated.get("content", tool_norm["content"])
                        tool_norm["quality_gate"] = gated.get("action")
                    return tool_norm
                if "content" in result:
                    return result
                elif "response" in result:
                    return {"content": result["response"], "sources": result.get("retrieved_knowledge", [])}
                else:
                    return {"content": str(result)}
            return {"content": str(result)}
        
        # 多个结果需要整合
        # 多结果整合前，先把 tool 输出稳定转换为文本，避免 LLM 收到大块结构化对象
        normalized_for_merge: List[Any] = []
        for r in successful_results:
            if isinstance(r, dict):
                tool_norm = self._normalize_tool_result(r)
                if tool_norm:
                    normalized_for_merge.append({"type": "tool", "content": tool_norm.get("content"), "skill_id": tool_norm.get("skill_id")})
                    continue
                if "content" in r:
                    normalized_for_merge.append({"type": "agent", "content": r.get("content")})
                    continue
            normalized_for_merge.append(r)

        response = await self.call_llm(
            [
                {
                    "role": "system",
                    "content": "你是一个结果整合专家。将多个医学分析结果整合为一个完整、连贯的响应。"
                },
                {"role": "user", "content": f"整合以下结果：\n{normalized_for_merge}"}
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

    @staticmethod
    def _rule_based_tool_intent(user_input: str) -> Optional[Dict[str, Any]]:
        """
        用于“稳定触发工具/技能”的规则兜底。
        目标：不依赖大模型意图识别也能把常见需求稳定路由到 tool agent。
        """
        text = (user_input or "").strip()
        if not text:
            return None

        def make(skill_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.95,
                "task_complexity": "simple",
                "tool": {
                    "skill_id": skill_id,
                    "params": params or {"text": text},
                },
            }

        # 化验单/检验结果
        lab_keywords = ["化验单", "检验结果", "检验报告", "血常规", "生化", "肝功能", "肾功能", "尿常规", "指标解读", "检验单"]
        if any(k in text for k in lab_keywords):
            lab_results = OrchestratorAgent._parse_lab_report(text)
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.95,
                "task_complexity": "simple",
                "tool": {
                    "skill_id": "skill_lab_interpretation",
                    "params": {"text": text, "lab_results": lab_results},
                },
            }

        # 分诊/挂号建议（优先走医学后端的 /triage 状态机）
        triage_keywords = ["分诊", "挂什么科", "挂号", "看什么科", "去哪个科", "需要急诊吗", "是否急诊"]
        if any(k in text for k in triage_keywords):
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.95,
                "task_complexity": "simple",
                "tool": {
                    "skill_id": "skill_medical_api_triage",
                    "params": {"prompt": text, "use_rag": True},
                },
            }

        # 临床建议/治疗方案（走 /clinical）
        clinical_keywords = ["治疗方案", "用药方案", "下一步治疗", "怎么治疗", "临床建议", "指南推荐", "联合用药"]
        if any(k in text for k in clinical_keywords):
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.9,
                "task_complexity": "simple",
                "tool": {
                    "skill_id": "skill_medical_api_clinical",
                    "params": {"prompt": text, "use_rag": True},
                },
            }

        # 医学写作（走 /write）
        writing_keywords = ["科普", "写一份", "撰写", "写个", "文章", "指南", "病历摘要", "出院小结", "随访计划文案"]
        if any(k in text for k in writing_keywords) and ("写" in text or "撰写" in text or "科普" in text):
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.9,
                "task_complexity": "simple",
                "tool": {
                    "skill_id": "skill_medical_api_write",
                    "params": {"prompt": text, "use_rag": True},
                },
            }

        # 个案管理计划（走 /management_plan）
        mp_keywords = ["管理计划", "个案管理", "每日任务", "随访计划", "康复计划", "术后", "用药指导", "未来一周"]
        if any(k in text for k in mp_keywords) and ("计划" in text or "每日" in text or "任务" in text):
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.9,
                "task_complexity": "simple",
                "tool": {
                    "skill_id": "skill_medical_api_management_plan",
                    "params": {"prompt": text, "use_rag": True, "return_rag_info": True},
                },
            }

        # 临床实验设计（走 /clinical_trial）
        trial_keywords = ["临床试验", "RCT", "随机对照", "样本量", "非劣效", "统计学方法", "试验方案"]
        if any(k.lower() in text.lower() for k in trial_keywords):
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.9,
                "task_complexity": "simple",
                "tool": {
                    "skill_id": "skill_medical_api_clinical_trial",
                    "params": {"prompt": text, "use_rag": True},
                },
            }

        # 症状自查
        symptom_keywords = ["症状自查", "我这个症状", "帮我分析症状", "症状分析"]
        if any(k in text for k in symptom_keywords):
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.9,
                "task_complexity": "simple",
                "tool": {"skill_id": "skill_symptom_checker", "params": {"text": text}},
            }

        # 药物相互作用
        drug_keywords = ["相互作用", "一起吃", "能否同服", "药物冲突"]
        if any(k in text for k in drug_keywords):
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.9,
                "task_complexity": "simple",
                "tool": {"skill_id": "skill_drug_interaction", "params": {"text": text}},
            }

        # 剂量计算
        dose_keywords = ["剂量", "用量", "怎么吃", "mg", "毫克", "每次", "每日"]
        if any(k in text for k in dose_keywords) and ("计算" in text or "换算" in text):
            return {
                "intent_type": "tool",
                "entities": [],
                "confidence": 0.9,
                "task_complexity": "simple",
                "tool": {"skill_id": "skill_dosage_calculator", "params": {"text": text}},
            }

        # 文献/指南
        if "文献" in text or "PubMed" in text or "研究" in text:
            return make("skill_literature_search")

        if "指南" in text or "共识" in text:
            return make("skill_clinical_guideline")

        return None
