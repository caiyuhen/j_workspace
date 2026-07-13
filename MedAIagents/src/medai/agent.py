"""
医学AI代理核心类
Medical AI Agent Core Class
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Generator
from loguru import logger


def _run_async(coro):
    """辅助函数：在已有或新事件循环中运行协程"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None:
        # 已有事件循环（如 Jupyter、FastAPI 等），创建新线程运行
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)

from .config import Config
from .llm.routing import LLMRouter
from .memory.system import MemorySystem
from .knowledge.base import MedicalKnowledgeBase
from .cdss.diagnosis import ClinicalDecisionSupport
from .emr.automation import EMRNoteGenerator, ICD10Coder
from .security.compliance import SecurityManager
from .mcp import MCPServerManager
from .tools.registry import ToolRegistry
from .tools.executor import ToolExecutor
from .tools.medical_tools import register_medical_tools
from .tools.system_tools import register_system_tools
from .planner.engine import TaskPlanner
from .agents.orchestrator import AgentOrchestrator
from .agents.specialized import (
    ClinicalAgent, ImagingAgent, ResearchAgent,
    WritingAgent, BioinformaticsAgent
)
from .sandbox.executor import CodeSandbox
from .evolution.learner import FeedbackCollector
from .evolution.optimizer import PromptOptimizer
from .evolution.tracker import PerformanceTracker
from .skills.registry import SkillRegistry
from .skills.executor import SkillExecutor
from .skills.learner import SkillLearner
from .skills.builtin import register_builtin_skills


class MedicalAgent:
    """医学AI代理核心类 - v0.6.0 增强版
    
    支持: MCP协议、工具调用、任务规划、多Agent编排、代码沙箱、自进化、Skills
    """
    
    def __init__(self, config_path: str = None, **kwargs):
        """初始化医学AI代理
        
        Args:
            config_path: 配置文件路径
            **kwargs: 额外配置参数
        """
        # 加载配置
        self.config = Config(config_path)
        
        # 初始化各子系统
        self.llm_router = LLMRouter(self.config)
        self.memory = MemorySystem(self.config)
        self.knowledge_base = MedicalKnowledgeBase(self.config)
        self.cdss = ClinicalDecisionSupport(self.config)
        self.emr_generator = EMRNoteGenerator(self.config)
        self.icd_coder = ICD10Coder(self.config)
        self.security = SecurityManager(self.config)
        
        # === v0.6.0 新增 Agent 基础设施 ===
        
        # MCP 多服务器管理
        self.mcp_manager = MCPServerManager()
        
        # 工具注册表与执行器
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        register_medical_tools(self.tool_registry)
        register_system_tools(self.tool_registry)
        
        # 任务规划器
        self.task_planner = TaskPlanner(self.llm_router)
        
        # 多 Agent 编排器
        self.agent_orchestrator = AgentOrchestrator()
        self._register_specialized_agents()
        
        # 代码沙箱
        self.code_sandbox = CodeSandbox()
        
        # 自进化系统
        self.feedback_collector = FeedbackCollector()
        self.prompt_optimizer = PromptOptimizer(self.llm_router)
        self.performance_tracker = PerformanceTracker()
        
        # === Skill 系统 ===
        self.skill_registry = SkillRegistry()
        self.skill_executor = SkillExecutor(
            skill_registry=self.skill_registry,
            llm_router=self.llm_router,
            tool_executor=self.tool_executor,
            agent_orchestrator=self.agent_orchestrator
        )
        self.skill_learner = SkillLearner(llm_router=self.llm_router)
        # 注册内置医学 Skills
        register_builtin_skills(self.skill_registry)
        
        # 会话信息
        self.current_user_id = kwargs.get('user_id', 'default')
        self.current_session_id = self.memory.create_session()
        
        # 系统提示词
        self.system_prompt = self._build_system_prompt()
        
        logger.info(f"MedicalAgent v0.6.0 initialized - Session: {self.current_session_id}")
    
    def _register_specialized_agents(self):
        """注册专科 Agent 到编排器"""
        agents = [
            ClinicalAgent(self.llm_router),
            ImagingAgent(self.llm_router),
            ResearchAgent(self.llm_router),
            WritingAgent(self.llm_router),
            BioinformaticsAgent(self.llm_router),
        ]
        for agent in agents:
            self.agent_orchestrator.register_agent(agent)
        logger.info(f"Registered {len(agents)} specialized agents")
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是MedAIagents医学AI助手，专门为医疗临床医生和医学研究人员设计。

你的核心功能包括：
1. 临床决策支持 - 基于症状和检查结果提供诊断建议
2. 医学知识检索 - 查询最新的医学指南和研究文献
3. 电子病历辅助 - 自动生成和提取病历信息
4. 用药安全检查 - 检查药物相互作用和剂量合理性

重要提示：
- 你的建议仅供参考，不能替代专业医生的诊断和治疗
- 对于临床决策，必须由合格的医疗专业人员做出
- 请始终提醒用户咨询医生的专业意见
- 在做出任何医疗建议前，必须说明这只是辅助建议

请用专业、严谨、清晰的语言回答医疗相关问题。
对于非医疗问题，请礼貌地说明你的专业范围。
"""
    
    def chat(self, user_input: str, use_knowledge: bool = True) -> str:
        """与医学AI代理对话
        
        Args:
            user_input: 用户输入
            use_knowledge: 是否使用知识库
        
        Returns:
            AI回复
        """
        # 记录用户消息
        self.memory.add_message('user', user_input)
        
        # 构建提示词
        messages = self._build_chat_prompt(user_input, use_knowledge)
        
        # 调用LLM
        try:
            response = _run_async(self.llm_router.chat(messages))
            self.memory.add_message('assistant', response)
            
            # 记录审计日志
            self.security.log_access(
                user_id=self.current_user_id,
                username='user',
                action='chat',
                resource_type='conversation',
                details={'input_length': len(user_input), 'output_length': len(response)}
            )
            
            return response
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"抱歉，处理您的请求时出现错误：{str(e)}"
    
    def _build_chat_prompt(self, user_input: str, use_knowledge: bool) -> List[Dict[str, str]]:
        """构建聊天提示词"""
        messages = [{'role': 'system', 'content': self.system_prompt}]
        
        # 添加相关的医学知识
        if use_knowledge:
            knowledge_results = self.knowledge_base.search(user_input, limit=3)
            if knowledge_results:
                context = "\n【相关医学知识】\n"
                for i, result in enumerate(knowledge_results, 1):
                    if 'title' in result:
                        context += f"{i}. {result['title']}\n"
                        if 'content' in result:
                            context += f"   {result['content'][:200]}...\n"
                context += "【请在回答中参考以上医学知识】\n\n"
                messages.append({'role': 'system', 'content': context})
        
        # 添加历史对话（最后5轮）
        history = self.memory.get_conversation_history(limit=10)
        messages.extend(history[1:])  # 跳过system消息
        
        messages.append({'role': 'user', 'content': user_input})
        
        return messages
    
    def diagnose(self, symptoms: List[str], lab_results: Dict[str, str] = None) -> Dict[str, Any]:
        """诊断辅助功能
        
        Args:
            symptoms: 症状列表
            lab_results: 实验室检查结果
        
        Returns:
            诊断结果
        """
        logger.info(f"Diagnosis request - Symptoms: {symptoms}")
        
        # 使用CDSS进行诊断
        diagnosis_result = self.cdss.diagnose(symptoms, lab_results)
        
        # 记录审计日志
        self.security.log_access(
            user_id=self.current_user_id,
            username='user',
            action='diagnosis',
            resource_type='clinical_decision_support',
            details={'symptoms_count': len(symptoms), 'has_lab_results': bool(lab_results)}
        )
        
        return diagnosis_result
    
    def check_medication_safety(
        self,
        medications: List[str],
        allergies: List[str] = None,
        doses: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """用药安全检查
        
        Args:
            medications: 药物列表
            allergies: 过敏史
            doses: 剂量信息
        
        Returns:
            安全性检查结果
        """
        logger.info(f"Medication safety check - Drugs: {medications}")
        
        result = self.cdss.check_medication_safety(medications, allergies, doses)
        
        # 记录审计日志
        self.security.log_access(
            user_id=self.current_user_id,
            username='user',
            action='medication_check',
            resource_type='medication_safety',
            details={'medications_count': len(medications)}
        )
        
        return result
    
    def generate_medical_note(
        self,
        note_type: str,
        patient_info: Dict[str, Any],
        clinical_data: Dict[str, Any]
    ) -> str:
        """生成医学文书
        
        Args:
            note_type: 文书类型 (admission, progress, discharge)
            patient_info: 患者信息
            clinical_data: 临床数据
        
        Returns:
            生成的医学文书
        """
        logger.info(f"Generating medical note - Type: {note_type}")
        
        # 对患者信息进行安全处理（去标识化）
        secured_patient_info = self.security.secure_data(patient_info, deidentify=True)
        
        if note_type == 'admission':
            note = self.emr_generator.generate_admission_note(
                patient_name=secured_patient_info.get('name', '患者'),
                gender=secured_patient_info.get('gender', '未知'),
                age=secured_patient_info.get('age', 0),
                chief_complaint=clinical_data.get('chief_complaint', ''),
                diagnosis=clinical_data.get('diagnosis', '')
            )
        elif note_type == 'progress':
            note = self.emr_generator.generate_progress_note(
                subjective=clinical_data.get('subjective', ''),
                temperature=clinical_data.get('temperature', 36.5),
                pulse=clinical_data.get('pulse', 72),
                respiration=clinical_data.get('respiration', 18),
                blood_pressure=clinical_data.get('blood_pressure', '120/80')
            )
        elif note_type == 'discharge':
            note = self.emr_generator.generate_discharge_note(
                patient_name=secured_patient_info.get('name', '患者'),
                gender=secured_patient_info.get('gender', '未知'),
                age=secured_patient_info.get('age', 0),
                admission_diagnosis=clinical_data.get('admission_diagnosis', ''),
                discharge_diagnosis=clinical_data.get('discharge_diagnosis', ''),
                discharge_orders=clinical_data.get('discharge_orders', '')
            )
        else:
            note = f"不支持的文书类型: {note_type}"
        
        # 记录审计日志
        self.security.log_access(
            user_id=self.current_user_id,
            username='user',
            action='generate_note',
            resource_type='emr_note',
            details={'note_type': note_type}
        )
        
        return note
    
    def get_icd10_code(self, diagnosis: str) -> Dict[str, Any]:
        """获取ICD-10编码
        
        Args:
            diagnosis: 诊断名称
        
        Returns:
            包含ICD-10编码的结果
        """
        code = self.icd_coder.get_icd10_code(diagnosis)
        
        if code:
            return {
                'diagnosis': diagnosis,
                'icd10_code': code,
                'found': True
            }
        else:
            # 搜索相关编码
            search_results = self.icd_coder.search_icd10(diagnosis)
            return {
                'diagnosis': diagnosis,
                'icd10_code': None,
                'found': False,
                'suggestions': search_results
            }
    
    def search_knowledge(self, query: str, limit: int = 5, use_pubmed: bool = False) -> List[Dict[str, Any]]:
        """搜索医学知识库
        
        Args:
            query: 搜索查询
            limit: 结果数量限制
            use_pubmed: 是否使用PubMed搜索
        
        Returns:
            知识条目列表
        """
        results = self.knowledge_base.search(query, limit, use_pubmed)
        
        # 记录审计日志
        self.security.log_access(
            user_id=self.current_user_id,
            username='user',
            action='knowledge_search',
            resource_type='medical_knowledge',
            details={'query': query, 'result_count': len(results)}
        )
        
        return results
    
    def switch_model(self, provider: str):
        """切换LLM提供商
        
        Args:
            provider: 提供商名称 (openai, anthropic, deepseek)
        """
        self.llm_router.switch_provider(provider)
        logger.info(f"Switched LLM provider to: {provider}")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.memory.get_conversation_history()
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        return self.memory.list_sessions()
    
    def switch_session(self, session_id: str):
        """切换会话"""
        self.memory.switch_session(session_id)
        self.current_session_id = session_id
        logger.info(f"Switched to session: {session_id}")
    
    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计日志"""
        return self.security.audit_logger.query_logs(limit=limit)
    
    def check_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检查数据合规性"""
        return self.security.check_compliance(data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取代理统计信息"""
        return {
            'version': '0.6.0',
            'current_session': self.current_session_id,
            'messages_in_session': len(self.memory.session_messages),
            'knowledge_base_size': self.knowledge_base.get_statistics(),
            'total_sessions': len(self.list_sessions()),
            'registered_tools': len(self.tool_registry.list_tools()),
            'registered_agents': len(self.agent_orchestrator._agents),
        }
    
    # === v0.6.0 新增方法 ===
    
    def chat_with_tools(self, user_input: str) -> str:
        """支持工具调用的对话模式
        
        LLM 可以自主选择并调用注册的工具来辅助回答。
        """
        self.memory.add_message('user', user_input)
        
        messages = self._build_chat_prompt(user_input, use_knowledge=True)
        tools = self.tool_registry.list_tools()
        
        try:
            content, tool_calls = _run_async(
                self.llm_router.chat_with_tools(messages, tools)
            )
            
            # 执行工具调用
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc.get('function', {}).get('name', '')
                    arguments = json.loads(tc.get('function', {}).get('arguments', '{}'))
                    try:
                        result = _run_async(self.tool_executor.execute(tool_name, arguments))
                        messages.append({
                            'role': 'tool',
                            'tool_call_id': tc.get('id', ''),
                            'name': tool_name,
                            'content': str(result)
                        })
                    except Exception as e:
                        logger.warning(f"Tool execution failed: {tool_name} - {e}")
                
                # 将工具结果返回给 LLM 获取最终回复
                content = _run_async(self.llm_router.chat(messages))
            
            self.memory.add_message('assistant', content)
            return content
        except Exception as e:
            logger.error(f"Chat with tools error: {e}")
            return f"抱歉，处理您的请求时出现错误：{str(e)}"
    
    def execute_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """在沙箱中安全执行代码
        
        Args:
            code: 代码字符串
            language: 编程语言 (目前仅支持 python)
        
        Returns:
            执行结果 {success, stdout, stderr, result}
        """
        logger.info(f"Code execution request - Language: {language}")
        if language == 'python':
            result = self.code_sandbox.execute_python(code)
        else:
            result = {'success': False, 'stdout': '', 'stderr': f'不支持的语言: {language}'}
        
        self.performance_tracker.record_execution(
            task_type='code_execution',
            duration_ms=0,
            success=result.get('success', False)
        )
        return result
    
    def plan_and_execute(self, user_request: str, context: str = "") -> Dict[str, Any]:
        """自动规划并执行任务
        
        将用户请求分解为子任务，按依赖关系并行执行。
        
        Args:
            user_request: 用户请求
            context: 额外上下文信息（可选）
        
        Returns:
            执行结果 {goal, subtasks, results, summary}
        """
        logger.info(f"Plan and execute - Request: {user_request}, Context: {context}")
        
        try:
            tools = self.tool_registry.list_tools()
            # 如果有上下文，拼接进请求中
            full_request = user_request
            if context:
                full_request = f"{user_request}\n\n## 上下文\n{context}"
            plan = _run_async(self.task_planner.plan(full_request, tools))
            executed_plan = _run_async(
                self.task_planner.execute(plan, self.tool_executor)
            )
            
            # 汇总结果
            results = {}
            for st in executed_plan.subtasks:
                results[st.id] = {
                    'description': st.description,
                    'status': st.status.value,
                    'result': st.result,
                    'error': st.error,
                }
            
            response = {
                'goal': executed_plan.goal,
                'subtasks': results,
                'summary': self._summarize_results(results),
                'deliverables': [],
            }
            
            # 自动检测并生成交付物
            deliverable_types = self._detect_deliverable_type(executed_plan.goal)
            if deliverable_types:
                logger.info(f"Auto-detected {len(deliverable_types)} deliverable types: {[d['type'] for d in deliverable_types]}")
                
                import os
                output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'exports')
                os.makedirs(output_dir, exist_ok=True)
                
                for dt in deliverable_types:
                    # 限制最多生成 2 个交付物，避免耗时过长
                    if len(response['deliverables']) >= 2:
                        break
                    
                    deliverable = self._generate_deliverable(
                        dt['type'], executed_plan.goal, results, output_dir
                    )
                    if deliverable:
                        response['deliverables'].append(deliverable)
            
            return response
        except Exception as e:
            logger.error(f"Plan and execute error: {e}")
            return {'goal': user_request, 'error': str(e)}
    
    def _should_auto_plan(self, user_input: str) -> bool:
        """使用 LLM 判断用户请求是否需要自动规划
        
        对于复杂、多步骤的任务自动触发规划，简单问题直接回答。
        
        Args:
            user_input: 用户输入
            
        Returns:
            是否需要自动规划
        """
        # 快速关键词预判断（避免简单问题也调用 LLM）
        simple_keywords = [
            '你好', 'hello', 'hi', '谢谢', '再见', '是什么', '是谁',
            '多少', '哪里', '为什么', '怎么读', '翻译',
        ]
        input_lower = user_input.strip().lower()
        for kw in simple_keywords:
            if input_lower == kw or input_lower == kw + '？' or input_lower == kw + '?':
                return False
        
        # 输入太短（<10字符），大概率是简单问题
        if len(user_input.strip()) < 10:
            return False
        
        # 使用 LLM 判断是否需要规划
        judge_prompt = f"""请判断以下用户请求是否需要分解为多个子任务来执行。

用户请求：{user_input}

判断标准：
- 需要规划：涉及多个步骤、多工具调用、复杂流程、方案设计、分析报告等
- 不需要规划：简单问答、单一概念解释、简单查询、问候等

请只回复 JSON，不要有其他内容：
{{"needs_plan": true或false, "reason": "简短理由"}}"""

        try:
            messages = [
                {"role": "system", "content": "你是一个任务复杂度判断助手，只输出 JSON。"},
                {"role": "user", "content": judge_prompt},
            ]
            response = _run_async(self.llm_router.chat(messages))
            
            # 解析 JSON
            resp_str = response.strip()
            if "```json" in resp_str:
                resp_str = resp_str.split("```json")[1].split("```")[0].strip()
            elif "```" in resp_str:
                resp_str = resp_str.split("```")[1].split("```")[0].strip()
            
            import json
            result = json.loads(resp_str)
            needs_plan = result.get('needs_plan', False)
            reason = result.get('reason', '')
            logger.info(f"Auto-plan judgment: needs_plan={needs_plan}, reason={reason}")
            return bool(needs_plan)
        except Exception as e:
            logger.warning(f"Auto-plan judgment failed: {e}, defaulting to no plan")
            return False
    
    def chat_with_auto_plan(self, user_input: str, use_knowledge: bool = True) -> Dict[str, Any]:
        """带自动任务规划的对话
        
        Hermes 风格：在对话中自动识别复杂请求，生成计划并执行。
        简单问题直接回答，复杂问题自动触发任务规划。
        
        Args:
            user_input: 用户输入
            use_knowledge: 是否使用知识库
            
        Returns:
            {
                "type": "simple" | "plan",
                "message": "直接回复内容",
                "plan": {  // 仅 type=plan 时存在
                    "goal": "任务目标",
                    "subtasks": {...},
                    "summary": "汇总"
                }
            }
        """
        # 记录用户消息
        self.memory.add_message('user', user_input)
        
        # 1. 判断是否需要自动规划
        needs_plan = self._should_auto_plan(user_input)
        
        if not needs_plan:
            # 简单问题，直接对话回答
            messages = self._build_chat_prompt(user_input, use_knowledge)
            try:
                response = _run_async(self.llm_router.chat(messages))
                self.memory.add_message('assistant', response)
                
                self.security.log_access(
                    user_id=self.current_user_id,
                    username='user',
                    action='chat',
                    resource_type='conversation',
                    details={'input_length': len(user_input), 'output_length': len(response)}
                )
                
                return {"type": "simple", "message": response}
            except Exception as e:
                logger.error(f"Chat error: {e}")
                return {"type": "simple", "message": f"抱歉，处理您的请求时出现错误：{str(e)}"}
        
        # 2. 复杂问题，自动生成任务计划并执行
        logger.info(f"Auto-planning triggered for: {user_input[:100]}")
        
        try:
            plan_result = self.plan_and_execute(user_input)
            
            if 'error' in plan_result:
                # 规划失败，降级为普通对话
                messages = self._build_chat_prompt(user_input, use_knowledge)
                response = _run_async(self.llm_router.chat(messages))
                self.memory.add_message('assistant', response)
                return {"type": "simple", "message": response}
            
            # 生成规划结果的文本摘要
            summary_text = self._format_plan_result(plan_result)
            self.memory.add_message('assistant', summary_text)
            
            self.security.log_access(
                user_id=self.current_user_id,
                username='user',
                action='auto_plan',
                resource_type='task_plan',
                details={'goal': plan_result.get('goal', ''), 'subtask_count': len(plan_result.get('subtasks', {}))}
            )
            
            # 提取交付物信息
            deliverables = plan_result.get('deliverables', [])
            
            return {
                "type": "plan",
                "message": summary_text,
                "plan": plan_result,
                "deliverables": deliverables
            }
        except Exception as e:
            logger.error(f"Auto-plan error: {e}")
            # 降级为普通对话
            try:
                messages = self._build_chat_prompt(user_input, use_knowledge)
                response = _run_async(self.llm_router.chat(messages))
                self.memory.add_message('assistant', response)
                return {"type": "simple", "message": response}
            except Exception:
                return {"type": "simple", "message": f"抱歉，处理请求时出现错误：{str(e)}"}
    
    def _format_plan_result(self, plan_result: Dict[str, Any]) -> str:
        """将规划结果格式化为可读的文本摘要
        
        Args:
            plan_result: plan_and_execute 的返回结果
            
        Returns:
            格式化的文本摘要
        """
        goal = plan_result.get('goal', '未知任务')
        subtasks = plan_result.get('subtasks', {})
        summary = plan_result.get('summary', '')
        
        text = f"## 任务规划：{goal}\n\n"
        text += "### 执行结果\n\n"
        
        completed = 0
        failed = 0
        for st_id, st_info in subtasks.items():
            status = st_info.get('status', 'unknown')
            desc = st_info.get('description', '')
            result = st_info.get('result', '')
            error = st_info.get('error', '')
            
            status_icon = "[OK]" if status == "completed" else "[FAIL]" if status == "failed" else "[--]"
            if status == "completed":
                completed += 1
            elif status == "failed":
                failed += 1
            
            text += f"- {status_icon} {desc}\n"
            if error:
                text += f"  错误: {error}\n"
            elif result and isinstance(result, dict):
                # 提取关键信息
                for k, v in result.items():
                    if k != 'description' and v:
                        text += f"  {k}: {str(v)[:200]}\n"
        
        text += f"\n**完成情况**: {completed}/{len(subtasks)} 成功"
        if failed > 0:
            text += f"，{failed} 个失败"
        text += "\n"
        
        if summary:
            text += f"\n### 总结\n{summary}\n"
        
        # 添加可下载交付物信息
        deliverables = plan_result.get('deliverables', [])
        if deliverables:
            text += "\n### 可下载交付物\n\n"
            for d in deliverables:
                filename = d.get('filename', '')
                label = d.get('label', '文件')
                size = d.get('size', 0)
                size_str = f"{size / 1024:.1f}KB" if size > 0 else ""
                text += f"- 📄 **{label}** ({filename}) {size_str}\n"
            text += "\n> 点击上方回复中的下载链接或前往「导出下载」页面获取文件\n"
        
        return text

    def auto_orchestrate(self, task: str) -> str:
        """自动编排多 Agent 协作完成任务
        
        根据任务内容自动选择合适的专科 Agent 协作。
        
        Args:
            task: 任务描述
        
        Returns:
            协作结果
        """
        logger.info(f"Auto orchestrate - Task: {task}")
        try:
            result = _run_async(
                self.agent_orchestrator.auto_orchestrate(task, self.task_planner)
            )
            return result
        except Exception as e:
            logger.error(f"Auto orchestrate error: {e}")
            return f"编排执行出错：{str(e)}"
    
    def delegate_to_agents(self, task: str, roles: List[str]) -> Dict[str, str]:
        """将任务分派给多个专科 Agent 并行执行
        
        Args:
            task: 任务描述
            roles: Agent 角色列表 ['clinical', 'imaging', 'research', ...]
        
        Returns:
            各 Agent 执行结果
        """
        return _run_async(self.agent_orchestrator.delegate(task, roles))
    
    def add_mcp_server(self, name: str, config: Dict[str, Any]) -> bool:
        """添加 MCP Server 连接
        
        Args:
            name: Server 名称
            config: 配置 {transport, command, args, url}
        
        Returns:
            是否成功
        """
        try:
            _run_async(self.mcp_manager.add_server(name, config))
            # 刷新工具列表
            tools = _run_async(self.mcp_manager.get_all_tools())
            logger.info(f"MCP Server '{name}' added, {len(tools)} tools available")
            return True
        except Exception as e:
            logger.error(f"Add MCP server failed: {e}")
            return False
    
    def record_feedback(self, task_id: str, feedback: str, rating: int):
        """记录用户反馈用于自进化"""
        self.feedback_collector.record_feedback(
            task_id=task_id,
            task_type='general',
            input_text='',
            output_text='',
            feedback=feedback,
            rating=rating
        )
    
    def _summarize_results(self, results: Dict[str, Any]) -> str:
        """汇总任务执行结果"""
        completed = sum(1 for r in results.values() if r.get('status') == 'completed')
        failed = sum(1 for r in results.values() if r.get('status') == 'failed')
        total = len(results)
        return f"任务执行完成: {completed}/{total} 成功, {failed}/{total} 失败"
    
    def _detect_deliverable_type(self, goal: str) -> List[Dict[str, Any]]:
        """根据任务目标自动检测应生成的交付物类型
        
        Args:
            goal: 任务目标描述
            
        Returns:
            交付物类型列表 [{type, label, format, description}]
        """
        goal_lower = goal.lower()
        candidates = []
        
        # 关键词匹配检测
        rule_map = [
            # (关键词列表, 交付物类型, 文件后缀, 显示标签)
            (['meta分析', 'meta-analysis', 'meta analysis', '荟萃分析', '系统综述'],
             'meta_analysis', 'xlsx', 'Meta分析结果表'),
            (['基金申请', '申请书', 'grant', 'nsfc', '国自然', '课题申请'],
             'grant', 'docx', '基金申请书'),
            (['rct', '临床试验', '试验方案', 'protocol', '随机对照'],
             'protocol', 'docx', '临床试验方案'),
            (['论文', 'paper', '文章', '论著', 'manuscript', '撰写论文'],
             'paper', 'docx', '医学论文'),
            (['幻灯片', 'ppt', 'presentation', '汇报', 'slides', '报告ppt'],
             'research_report', 'pptx', '科研汇报PPT'),
            (['经费预算', '预算表', 'budget', '经费'],
             'budget', 'xlsx', '经费预算表'),
            (['生存分析', 'survival', 'kaplan', 'km曲线', 'cox'],
             'survival', 'xlsx', '生存分析数据'),
            (['response letter', '审稿回复', '回复信', 'rebuttal'],
             'response_letter', 'docx', '审稿回复信'),
            (['影像', 'imaging', '放射', 'ct', 'mri', '超声'],
             'teaching', 'pptx', '影像教学PPT'),
            (['生信', '生物信息', 'bioinformatics', '基因组', '转录组'],
             'bioinformatics', 'pptx', '生信分析报告PPT'),
            (['期刊', 'journal', '投稿期刊'],
             'journal_db', 'xlsx', '期刊数据库'),
        ]
        
        for keywords, dtype, fmt, label in rule_map:
            if any(kw in goal_lower for kw in keywords):
                candidates.append({
                    'type': dtype,
                    'format': fmt,
                    'label': label,
                    'description': f'根据"{goal[:50]}..."自动生成的{label}'
                })
        
        return candidates
    
    def _check_deliverable_hard_rules(self, dtype: str, data: Dict[str, Any]) -> tuple:
        """代码级硬规则校验：检查交付物数据是否满足最低质量标准
        
        Returns:
            (passed: bool, issues: list[str])
        """
        issues = []
        
        def _len(text) -> int:
            """计算字符串长度（中文字符算1个）"""
            return len(str(text)) if text else 0
        
        def _list_len(obj) -> int:
            """安全获取列表长度"""
            return len(obj) if isinstance(obj, list) else 0
        
        if dtype == 'paper':
            refs = _list_len(data.get('references'))
            if refs < 15:
                issues.append(f"参考文献数量不足：{refs}条（要求≥15条）")
            if _len(data.get('introduction')) < 800:
                issues.append(f"引言字数不足：{_len(data.get('introduction'))}字（要求≥800字）")
            if _len(data.get('methods')) < 800:
                issues.append(f"方法字数不足：{_len(data.get('methods'))}字（要求≥800字）")
            if _len(data.get('results')) < 600:
                issues.append(f"结果字数不足：{_len(data.get('results'))}字（要求≥600字）")
            if _len(data.get('discussion')) < 800:
                issues.append(f"讨论字数不足：{_len(data.get('discussion'))}字（要求≥800字）")
            if _len(data.get('abstract')) < 100:
                issues.append(f"摘要字数不足：{_len(data.get('abstract'))}字（要求≥100字）")
        
        elif dtype == 'grant':
            if _len(data.get('rationale')) < 1200:
                issues.append(f"立项依据字数不足：{_len(data.get('rationale'))}字（要求≥1200字）")
            if _len(data.get('research_content')) < 800:
                issues.append(f"研究内容字数不足：{_len(data.get('research_content'))}字（要求≥800字）")
            if _len(data.get('methodology')) < 800:
                issues.append(f"研究方案字数不足：{_len(data.get('methodology'))}字（要求≥800字）")
            budget = data.get('budget', {})
            items = _list_len(budget.get('items')) if isinstance(budget, dict) else 0
            if items < 8:
                issues.append(f"经费预算科目不足：{items}个（要求≥8个）")
        
        elif dtype == 'protocol':
            inclusion = _list_len(data.get('inclusion_criteria'))
            if inclusion < 8:
                issues.append(f"入选标准不足：{inclusion}条（要求≥8条）")
            exclusion = _list_len(data.get('exclusion_criteria'))
            if exclusion < 8:
                issues.append(f"排除标准不足：{exclusion}条（要求≥8条）")
            if _len(data.get('statistical_analysis')) < 400:
                issues.append(f"统计方法描述不足：{_len(data.get('statistical_analysis'))}字（要求≥400字）")
        
        elif dtype == 'meta_analysis':
            studies = _list_len(data.get('studies'))
            if studies < 8:
                issues.append(f"纳入研究数量不足：{studies}个（要求≥8个）")
        
        elif dtype == 'budget':
            items = _list_len(data.get('items'))
            if items < 8:
                issues.append(f"预算科目不足：{items}个（要求≥8个）")
        
        elif dtype == 'survival':
            records = _list_len(data)
            if records < 30:
                issues.append(f"数据记录不足：{records}条（要求≥30条）")
        
        elif dtype == 'response_letter':
            responses = _list_len(data.get('responses'))
            if responses < 3:
                issues.append(f"回复审稿人数量不足：{responses}个（要求≥3个）")
            for i, r in enumerate(data.get('responses', [])[:responses]):
                if _len(r.get('response', '')) < 200:
                    issues.append(f"Reviewer #{i+1} 回复字数不足：{_len(r.get('response', ''))}字（要求≥200字）")
        
        elif dtype == 'research_report':
            for field in ['background', 'methods', 'results', 'discussion', 'conclusions']:
                items = _list_len(data.get(field))
                if items < 4:
                    issues.append(f"{field} 内容点不足：{items}条（要求≥4条）")
        
        elif dtype == 'teaching':
            findings = data if isinstance(data, list) else []
            if _list_len(findings) < 5:
                issues.append(f"征象数量不足：{_list_len(findings)}个（要求≥5个）")
            for i, f in enumerate(findings[:_list_len(findings)]):
                if _len(f.get('description', '')) < 100:
                    issues.append(f"征象{i+1}描述不足：{_len(f.get('description', ''))}字（要求≥100字）")
        
        elif dtype == 'bioinformatics':
            for field in ['sample_info', 'mutation_summary', 'pathways', 'survival', 'conclusions']:
                items = _list_len(data.get(field))
                if items < 4:
                    issues.append(f"{field} 内容点不足：{items}条（要求≥4条）")
        
        elif dtype == 'journal_db':
            journals = data if isinstance(data, list) else []
            if _list_len(journals) < 15:
                issues.append(f"期刊数量不足：{_list_len(journals)}个（要求≥15个）")
        
        passed = len(issues) == 0
        return passed, issues
    
    def _generate_deliverable(self, dtype: str, goal: str, subtasks: Dict[str, Any], output_dir: str) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成交付物数据并导出为文件（增强版：内容详实、数据丰富）

        Args:
            dtype: 交付物类型
            goal: 任务目标
            subtasks: 子任务结果
            output_dir: 输出目录

        Returns:
            交付物元数据 {type, label, format, filename, filepath} 或 None
        """
        try:
            import os
            from datetime import datetime

            # 构建 LLM 提示词，让 LLM 生成导出所需的结构化数据
            # 扩充上下文长度，从3000字符增加到12000，充分利用子任务结果
            subtasks_json = json.dumps(subtasks, ensure_ascii=False, indent=2)
            subtasks_summary = subtasks_json[:12000] if len(subtasks_json) > 12000 else subtasks_json
            if len(subtasks_json) > 12000:
                subtasks_summary += "\n...（后续结果已截断）"

            # 根据不同类型构建不同的生成提示（增强版：详细字段要求、字数要求、数据要求）
            type_prompts = {
                'paper': {
                    'exporter_fn': 'export_paper',
                    'exporter_class': 'PaperExporter',
                    'format': 'docx',
                    'label': '医学论文',
                    'system': '你是一位资深医学论文写作专家，擅长撰写高质量的IMRaD结构医学论文。你的输出必须专业、详实、数据充分，符合SCI期刊投稿标准。',
                    'data_schema': '{"title": "论文标题（准确反映研究内容）", "authors": "作者姓名（如：张三, 李四, 王五）", "abstract": "结构化摘要：目的、方法、结果、结论，300-500字", "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"], "introduction": "引言：研究背景、国内外现状、研究意义、研究目的。不少于800字，需引用相关文献支撑论述", "methods": "方法：研究设计、纳入排除标准、干预措施、终点指标、统计方法。不少于800字，需详细到可重复", "results": "结果：基线特征、主要终点、次要终点、亚组分析、安全性。不少于600字，需包含具体数据", "discussion": "讨论：主要发现解读、与现有研究比较、研究优势、局限性、临床意义、未来方向。不少于800字", "conclusion": "结论：简明总结核心发现，200-300字", "references": ["1. 作者. 标题. 期刊名. 年份;卷(期):页码.", "2. ...（至少15条参考文献）"]}',
                    'quality_requirements': '1. 摘要300-500字，包含目的/方法/结果/结论四部分；2. 引言≥800字，需论述研究背景和意义；3. 方法≥800字，详细到可重复；4. 结果≥600字，包含具体数值；5. 讨论≥800字，深入分析；6. 参考文献≥15条'
                },
                'grant': {
                    'exporter_fn': 'export_proposal',
                    'exporter_class': 'GrantProposalExporter',
                    'format': 'docx',
                    'label': '基金申请书',
                    'system': '你是一位资深的国家自然科学基金申请书撰写专家，擅长撰写高质量的科研基金申请书。你的输出必须逻辑严密、论证充分、创新点突出。',
                    'data_schema': '{"title": "项目名称（准确、简洁、有吸引力）", "grant_type": "NSFC/省基金/院基金", "research_area": "具体研究领域", "applicant": "申请人姓名", "institution": "依托单位", "rationale": "立项依据：研究背景、国内外进展、存在问题、科学假说。不少于1200字，需引用关键文献", "research_content": "研究内容：具体研究内容1、2、3，每条详细描述。总计不少于800字", "objectives": "研究目标：总体目标和具体目标，清晰可考核。200-400字", "key_problems": "关键科学问题：1-3个核心科学问题，每个问题分析深入。400-600字", "methodology": "研究方案：技术路线、实验设计、数据分析方法。不少于800字，需具体到实验步骤", "feasibility": "可行性分析：前期工作基础、技术条件、团队能力、资源保障。400-600字", "innovation": "创新点：理论创新、方法创新、应用创新。200-400字", "timeline": "年度计划：第1年...第2年...第3年...，每年具体任务和考核指标", "expected_outcomes": "预期成果：论文、专利、人才培养、临床应用等。200-400字", "budget": {"total": 50, "items": [{"name": "设备费", "amount": 10, "notes": "具体设备名称和用途说明"}, {"name": "材料费", "amount": 8, "notes": "试剂、耗材等"}, {"name": "测试化验加工费", "amount": 6, "notes": "外送检测费用"}, {"name": "差旅/会议费", "amount": 5, "notes": "学术交流"}, {"name": "出版/文献费", "amount": 3, "notes": "论文发表、查新"}, {"name": "劳务费", "amount": 12, "notes": "研究生助研津贴"}, {"name": "专家咨询费", "amount": 4, "notes": "专家论证"}, {"name": "间接费用", "amount": 2, "notes": "管理费"}]}}',
                    'quality_requirements': '1. 立项依据≥1200字，充分论证科学问题；2. 研究内容≥800字，具体可操作；3. 研究方案≥800字，详细到实验步骤；4. 关键科学问题分析深入；5. 创新点明确突出；6. 经费预算科目完整、理由充分'
                },
                'protocol': {
                    'exporter_fn': 'export_protocol',
                    'exporter_class': 'ProtocolExporter',
                    'format': 'docx',
                    'label': '临床试验方案',
                    'system': '你是一位资深的临床试验方案设计专家，熟悉ICH-GCP、CONSORT等国际标准。你的输出必须严谨、规范、可执行。',
                    'data_schema': '{"study_info": {"title": "方案全称", "study_type": "多中心/单中心 RCT", "phase": "I/II/III期", "indication": "具体适应症", "duration_months": 24, "sponsor": "申办方", "protocol_version": "1.0", "protocol_date": "2024-01-01"}, "study_objectives": {"primary": "主要目的：详细描述", "secondary": ["次要目的1：详细描述", "次要目的2：详细描述"]}, "endpoints": {"primary": "主要终点：具体指标、测量方法、时间点", "secondary": ["次要终点1：具体指标", "次要终点2：具体指标"]}, "inclusion_criteria": ["1. 年龄18-75岁", "2. 经组织学/细胞学确诊的...", "3. ECOG评分0-1分", "4. 预期生存期≥3个月", "5. 足够的器官功能（中性粒细胞≥1.5×10^9/L，血小板≥100×10^9/L...）", "6. 自愿签署知情同意书", "7. ...（至少8条详细入选标准）"], "exclusion_criteria": ["1. 既往接受过同类药物治疗", "2. 合并其他恶性肿瘤", "3. 严重心肺功能不全", "4. 活动性感染", "5. 妊娠或哺乳期女性", "6. 已知对研究药物过敏", "7. ...（至少8条详细排除标准）"], "study_design": {"randomization": "分层区组随机化，按...分层", "blinding": "双盲/单盲/开放", "treatment_groups": [{"name": "试验组", "intervention": "具体给药方案：剂量、途径、频次、疗程", "control": "对照药物和方案"}, {"name": "对照组", "intervention": "...", "control": "..."}]}, "sample_size": {"calculation": "详细样本量计算过程和公式", "total": 200, "per_group": 100, "dropout_rate": "20%", "power": "80%", "alpha": "双侧0.05"}, "statistical_analysis": "详细统计分析方法：主要终点分析方法、次要终点、亚组分析、期中分析、缺失数据处理、多重性校正。不少于400字", "safety": {"ae_definition": "不良事件定义和分级标准（CTCAE v5.0）", "sae_reporting": "严重不良事件报告流程和时限", "dsmc": "数据安全监察委员会组成和职责"}, "ethical_considerations": {"informed_consent": "知情同意过程和文件要点", "ethics_committee": "伦理审查委员会", "data_protection": "受试者数据保护措施"}}',
                    'quality_requirements': '1. 入选标准≥8条，具体可执行；2. 排除标准≥8条，覆盖安全性和有效性；3. 干预方案具体到剂量/途径/频次；4. 样本量计算有公式和参数；5. 统计方法≥400字，涵盖主要/次要/亚组分析；6. 安全性监测方案完整'
                },
                'meta_analysis': {
                    'exporter_fn': 'export_meta_analysis',
                    'exporter_class': 'MetaAnalysisExporter',
                    'format': 'xlsx',
                    'label': 'Meta分析结果表',
                    'system': '你是一位资深的循证医学和Meta分析专家，熟悉Cochrane系统评价方法和RevMan软件。你的输出必须数据准确、统计规范。',
                    'data_schema': '{"studies": [{"name": "作者, 年份", "a_events": 50, "a_total": 100, "b_events": 30, "b_total": 100, "effect_size": 1.5, "ci_lower": 1.1, "ci_upper": 2.0, "weight": "25%", "quality": "RCT, Jadad=5分"}, {"name": "作者2, 年份", "a_events": 45, "a_total": 90, "b_events": 25, "b_total": 85, "effect_size": 1.6, "ci_lower": 1.0, "ci_upper": 2.4, "weight": "20%", "quality": "RCT, Jadad=4分"}, {"name": "...（至少8-12个真实研究数据）"}], "pooled_effect": 1.45, "ci_lower": 1.15, "ci_upper": 1.75, "i_squared": "42%", "q_statistic": 15.3, "q_df": 9, "q_pvalue": "0.08", "model": "Random-effects (DerSimonian-Laird)", "publication_bias": {"egger_p": "0.12", "beggs_p": "0.25", "funnel_plot": "对称", "trim_fill": "无需填补"}, "sensitivity": [{"analysis": "剔除低质量研究", "pooled_effect": 1.48, "ci_lower": 1.18, "ci_upper": 1.78}, {"analysis": "固定效应模型", "pooled_effect": 1.42, "ci_lower": 1.14, "ci_upper": 1.70}], "subgroup": [{"factor": "样本量", "level": ">100例", "pooled_effect": 1.5, "ci_lower": 1.2, "ci_upper": 1.8, "studies": 5}, {"factor": "样本量", "level": "≤100例", "pooled_effect": 1.3, "ci_lower": 0.9, "ci_upper": 1.7, "studies": 5}]}',
                    'quality_requirements': '1. 纳入研究≥8个，数据完整；2. 每个研究包含效应量和95%CI；3. 包含异质性检验（I²、Q统计量）；4. 包含发表偏倚评估（Egger、Begg）；5. 包含敏感性分析；6. 包含亚组分析'
                },
                'budget': {
                    'exporter_fn': 'export_budget',
                    'exporter_class': 'BudgetExporter',
                    'format': 'xlsx',
                    'label': '经费预算表',
                    'system': '你是一位资深的科研经费预算编制专家，熟悉国家自然科学基金等各类科研项目的经费管理办法。',
                    'data_schema': '{"title": "XX项目经费预算表", "total": 50, "currency": "万元", "items": [{"name": "设备费", "amount": 10.0, "percentage": "20%", "notes": "具体设备名称：高性能液相色谱仪（8万）、低温离心机（2万）", "details": [{"item": "液相色谱仪", "spec": "Agilent 1260 Infinity II", "unit_price": 8.0, "quantity": 1, "total": 8.0}]}, {"name": "材料费", "amount": 8.0, "percentage": "16%", "notes": "实验试剂、耗材、细胞培养基等", "details": [{"item": "胎牛血清", "spec": "Gibco", "unit_price": 0.3, "quantity": 10, "total": 3.0}]}, {"name": "测试化验加工费", "amount": 6.0, "percentage": "12%", "notes": "外送基因检测、质谱分析等", "details": [{"item": "全外显子测序", "spec": "30X", "unit_price": 0.4, "quantity": 10, "total": 4.0}]}, {"name": "差旅/会议费", "amount": 5.0, "percentage": "10%", "notes": "参加国内学术会议、调研差旅", "details": [{"item": "学术会议注册费", "spec": "CSCO年会", "unit_price": 0.2, "quantity": 5, "total": 1.0}]}, {"name": "出版/文献/信息传播费", "amount": 3.0, "percentage": "6%", "notes": "论文发表APC、查新、软件授权", "details": [{"item": "论文版面费", "spec": "OA期刊", "unit_price": 1.0, "quantity": 2, "total": 2.0}]}, {"name": "劳务费", "amount": 12.0, "percentage": "24%", "notes": "研究生助研津贴、临时聘用人员", "details": [{"item": "硕士研究生助研津贴", "spec": "2人×3年", "unit_price": 2.0, "quantity": 6, "total": 12.0}]}, {"name": "专家咨询费", "amount": 4.0, "percentage": "8%", "notes": "项目论证、方案评审专家费用", "details": [{"item": "专家咨询", "spec": "高级专家", "unit_price": 0.2, "quantity": 20, "total": 4.0}]}, {"name": "间接费用", "amount": 2.0, "percentage": "4%", "notes": "依托单位管理费", "details": [{"item": "管理费", "spec": "按直接费用4%计提", "unit_price": 2.0, "quantity": 1, "total": 2.0}]}]}',
                    'quality_requirements': '1. 科目完整，覆盖NSFC全部科目；2. 每个科目有明细项；3. 每项有单价、数量、合计；4. 占比合理，符合NSFC规定；5. 理由说明充分'
                },
                'survival': {
                    'exporter_fn': 'export_survival_data',
                    'exporter_class': 'SurvivalDataExporter',
                    'format': 'xlsx',
                    'label': '生存分析数据',
                    'system': '你是一位资深的生物统计学家，擅长生存分析和临床试验数据分析。你的输出必须数据真实、格式规范。',
                    'data_schema': '[{"patient_id": "P001", "time": 12.5, "event": 1, "group": "实验组", "age": 55, "gender": "男", "stage": "III", "ecog": 1, "biomarker_positive": 1, "prior_therapy": 0, "note": "疾病进展"}, {"patient_id": "P002", "time": 8.0, "event": 0, "group": "对照组", "age": 62, "gender": "女", "stage": "IV", "ecog": 2, "biomarker_positive": 0, "prior_therapy": 1, "note": "删失"}, {"patient_id": "P003", "time": 24.0, "event": 1, "group": "实验组", "age": 48, "gender": "男", "stage": "II", "ecog": 0, "biomarker_positive": 1, "prior_therapy": 0, "note": "死亡"}, {"patient_id": "...（至少30-50条模拟数据，覆盖不同亚组）"}]',
                    'quality_requirements': '1. 数据记录≥30条；2. 覆盖实验组和对照组；3. 包含time、event、group等核心字段；4. 包含协变量（年龄、分期、ECOG等）；5. 数据分布合理，有事件和删失'
                },
                'response_letter': {
                    'exporter_fn': 'export_response_letter',
                    'exporter_class': 'ResponseLetterExporter',
                    'format': 'docx',
                    'label': '审稿回复信',
                    'system': '你是一位资深的学术期刊编辑和审稿回复信撰写专家，擅长撰写礼貌、专业、有针对性的Response Letter。',
                    'data_schema': '{"manuscript_id": "MS-2024-001", "title": "论文完整标题", "authors": "作者1, 作者2, 作者3", "journal": "投稿期刊名称", "date": "2024-01-15", "opening": "尊敬的编辑和审稿人：感谢您们对本稿件的认真审阅和宝贵意见。我们已根据审稿意见逐条修改，修改内容在修订稿中以红色标注。", "responses": [{"reviewer": "Reviewer #1", "comment": "审稿意见原文：主要关注点的详细描述", "response": "尊敬的审稿人，感谢您的宝贵意见。我们已在修订稿中进行了以下修改：...（回复不少于200字，具体说明修改内容和位置）", "changes": "具体修改：在Results部分第3段增加了...，在Table 2中补充了..."}, {"reviewer": "Reviewer #2", "comment": "对统计方法的质疑：为什么使用Log-rank检验而不是...", "response": "感谢您的专业建议。我们重新分析了数据，现在同时报告了Log-rank检验和...的结果。具体修改如下：...", "changes": "在Methods部分更新了统计分析段落（第2.4节），在Results部分补充了敏感性分析结果（Figure S1）。"}, {"reviewer": "Editor", "comment": "建议补充更多关于研究局限性的讨论", "response": "感谢您的建议。我们在Discussion部分增加了Limitations小节，详细讨论了本研究的样本量限制、单中心设计、随访时间等局限性...", "changes": "Discussion部分新增第4节Limitations，约300字。"}, {"reviewer": "...（至少覆盖3-5个审稿人的全部意见）"}], "closing": "再次感谢编辑和审稿人的宝贵时间和专业意见。我们相信经过修改，稿件质量有了显著提升，期待您的进一步反馈。此致敬礼！"}',
                    'quality_requirements': '1. 覆盖所有审稿人（至少3个审稿人+编辑）；2. 每条回复≥200字，具体且有针对性；3. 每条意见都有明确的修改说明；4. 语气礼貌专业；5. 修改内容具体到章节/图表/行号'
                },
                'research_report': {
                    'exporter_fn': 'export_research_report',
                    'exporter_class': 'ResearchPresentationExporter',
                    'format': 'pptx',
                    'label': '科研汇报PPT',
                    'system': '你是一位资深的学术汇报PPT制作专家，擅长将复杂的研究内容转化为结构清晰、内容详实的学术演示文稿。',
                    'data_schema': '{"title": "汇报标题（醒目、准确）", "subtitle": "副标题：研究类型+单位+日期", "background": ["研究背景1：疾病负担和未满足需求，详细描述", "研究背景2：现有治疗的局限性，数据支撑", "研究背景3：本研究的科学假说和创新点", "研究背景4：国内外研究现状和本研究的定位"], "methods": ["研究设计：多中心、随机、双盲、对照试验", "纳入排除标准：详细描述目标人群", "干预方案：实验组和对照组具体给药方案", "终点指标：主要终点和次要终点定义", "统计方法：样本量、分析集、统计检验"], "results": ["基线特征：两组均衡性比较，具体数值", "主要终点：HR=0.65, 95%CI 0.48-0.89, p=0.003", "次要终点：PFS、ORR、DOR等具体数据", "亚组分析：森林图关键结果", "安全性：TRAE发生率、≥3级AE、特别关注AE"], "discussion": ["主要发现解读：与现有证据的一致性", "临床意义：对临床实践的影响", "研究优势：设计严谨、样本量大、随访充分", "研究局限性：单中心、开放标签等", "未来方向：后续研究计划"], "conclusions": ["核心结论1：主要终点的临床意义", "核心结论2：安全性特征总结", "核心结论3：对临床实践的建议"], "acknowledgments": ["感谢研究团队和参与中心", "感谢基金资助（项目编号）", "声明利益冲突和伦理审批"]}',
                    'quality_requirements': '1. 每页PPT的内容点≥4条；2. 每条内容具体、有数据支撑；3. 结果部分包含具体统计值；4. 背景部分论述充分；5. 讨论部分深入分析'
                },
                'teaching': {
                    'exporter_fn': 'export_teaching',
                    'exporter_class': 'ImagingTeachingExporter',
                    'format': 'pptx',
                    'label': '影像教学PPT',
                    'system': '你是一位资深的医学影像科主任医师和教学专家，擅长制作高质量的影像征象教学PPT。',
                    'data_schema': '[{"name": "磨玻璃结节（GGN）", "description": "肺内局限性密度增高影，血管和支气管纹理仍可见。病理基础为肺泡壁增厚或肺泡腔不完全填充。分为纯磨玻璃结节（pGGN）和混杂性磨玻璃结节（mGGN）。", "modalities": ["CT（HRCT为金标准）", "PET-CT（SUV值通常较低）"], "anatomy": ["右肺上叶", "左肺上叶", "双肺多发"], "diseases": ["早期肺腺癌（AIS/MIA）", "局灶性纤维化", "出血", "炎症"], "severity": "pGGN恶性率约18%，mGGN恶性率约63%", "differential": ["AIS：圆形/类圆形，边界清楚，密度均匀", "MIA：出现实性成分，分叶/毛刺", "炎症：短期内变化，抗感染后缩小"], "management": "≤5mm：年度随访；5-8mm：3-6月复查；>8mm或增长：考虑活检或手术"}, {"name": "...（至少5-8个典型征象，每个征象描述详细）"}]',
                    'quality_requirements': '1. 征象数量≥5个；2. 每个征象描述≥100字；3. 包含影像学表现、病理基础、鉴别诊断、处理建议；4. 包含相关疾病列表；5. 数据准确（恶性率、随访策略等）'
                },
                'bioinformatics': {
                    'exporter_fn': 'export_bioinformatics_report',
                    'exporter_class': 'BioinformaticsReportExporter',
                    'format': 'pptx',
                    'label': '生信分析报告PPT',
                    'system': '你是一位资深的生物信息学分析专家，擅长多组学数据分析和可视化汇报。',
                    'data_schema': '{"title": "多组学整合分析报告", "subtitle": "项目名称 | 分析日期 | 分析平台", "sample_info": ["样本来源：XX癌组织及配对癌旁组织", "样本量：实验组50例，对照组50例", "测序策略：WES（肿瘤100X，正常30X）+ RNA-seq", "质控：Q30≥85%，比对率≥95%"], "mutation_summary": ["突变负荷：TMB中位数8.2 mut/Mb（范围2.1-34.5）", "驱动突变：TP53（42%）、KRAS（28%）、EGFR（18%）", "突变特征：Signature 4（吸烟相关）占主导", "CNV：8q扩增（MYC）、17p缺失（TP53）"], "pathways": ["富集通路1：PI3K-AKT信号通路（FDR=2.3e-5）", "富集通路2：细胞周期调控（FDR=8.1e-4）", "富集通路3：DNA损伤修复（FDR=1.2e-3）", "GSEA结果：EMT和血管生成显著激活"], "survival": ["OS分析：高TMB组中位OS 28.5月 vs 低TMB组 16.2月（HR=0.52, p=0.008）", "PFS分析：PI3K突变组中位PFS 9.3月 vs 野生型 14.1月（HR=1.68, p=0.012）", "多因素分析：TMB、分期、ECOG为独立预后因素"], "conclusions": ["核心发现1：TP53/KRAS共突变与免疫治疗抵抗相关", "核心发现2：PI3K通路激活是潜在治疗靶点", "核心发现3：TMB可作为预后生物标志物"], "recommendations": ["建议1：针对PI3K突变患者开展靶向治疗研究", "建议2：验证TMB作为免疫治疗预测标志物", "建议3：扩大样本量进行外部验证"]}',
                    'quality_requirements': '1. 每部分≥4条具体内容；2. 包含具体统计值（p值、HR、FDR等）；3. 突变数据有频率和具体基因；4. 通路分析有统计学指标；5. 生存分析有具体数值'
                },
                'journal_db': {
                    'exporter_fn': 'export_journals',
                    'exporter_class': 'JournalDatabaseExporter',
                    'format': 'xlsx',
                    'label': '期刊数据库',
                    'system': '你是一位资深的医学期刊投稿顾问，熟悉各领域的SCI期刊情况和投稿策略。',
                    'data_schema': '[{"name": "Journal of Clinical Oncology", "abbreviation": "JCO", "impact_factor": 45.3, "jcr_quartile": "Q1", "cas_quartile": "Q1", "field": "肿瘤学/临床肿瘤", "oa_policy": "混合OA（APC $4000）", "review_period": "初审2-3周，外审4-8周", "acceptance_rate": "约15%", "article_types": ["Original Research", "Clinical Trial", "Review"], "special_requirements": "需要临床试验注册号，统计方法需详细", "website": "ascopubs.org/journal/jco"}, {"name": "Lancet Oncology", "abbreviation": "Lancet Oncol", "impact_factor": 41.6, "jcr_quartile": "Q1", "cas_quartile": "Q1", "field": "肿瘤学", "oa_policy": "混合OA（APC $6300）", "review_period": "初审1-2周，外审6-10周", "acceptance_rate": "约10%", "article_types": ["Article", "Review", "Comment"], "special_requirements": "摘要≤300字，图表≤6个", "website": "thelancet.com/journals/lanonc"}, {"name": "...（至少15-20个相关期刊）"}]',
                    'quality_requirements': '1. 期刊数量≥15个；2. 每个期刊信息完整（IF、分区、审稿周期、接收率）；3. 包含不同IF层次（高/中/低）；4. 包含OA政策和费用；5. 包含特殊投稿要求'
                }
            }

            if dtype not in type_prompts:
                logger.warning(f"Unknown deliverable type: {dtype}")
                return None

            tp = type_prompts[dtype]

            # ========== Loop 质量检验：生成 → 硬规则检查 → LLM自评分 → 不通过则迭代优化 ==========
            max_quality_rounds = 5
            quality_pass_score = 8  # 满分10分，≥8分通过（提高门槛）
            data = None
            last_score = 0
            last_review = ""
            hard_rules_passed = False

            for quality_round in range(max_quality_rounds):
                if quality_round == 0:
                    # 首轮生成
                    gen_prompt = f"""根据以下任务目标和子任务执行结果，生成一份高质量、内容详实的【{tp['label']}】。

## 任务目标
{goal}

## 子任务执行结果（请充分利用这些详细信息）
{subtasks_summary}

## 内容质量要求（必须严格遵守）
1. **内容详实**：每个字段/章节必须包含充分的内容，不可敷衍或只写框架
2. **数据丰富**：尽可能包含具体数据、统计值、病例数、百分比等量化信息
3. **专业深度**：使用专业术语，体现医学/科研领域的专业水平，不可泛泛而谈
4. **结构完整**：严格按照要求的JSON Schema输出，确保所有字段都有实质性内容
5. **中文撰写**：所有内容使用中文撰写（英文术语、期刊名、基因名保留原文）

## 各字段详细度要求
{tp['quality_requirements']}

## 输出格式
请严格按照以下 JSON Schema 格式输出数据。只输出 JSON 数据，不要包含任何其他说明文字。
注意：JSON中的字符串值必须是完整、详细的内容，不能是简短的占位符。

```json
{tp['data_schema']}
```"""
                    messages = [
                        {"role": "system", "content": tp['system']},
                        {"role": "user", "content": gen_prompt},
                    ]
                else:
                    # 迭代优化：附带评语让 LLM 改进
                    gen_prompt = f"""你之前生成的【{tp['label']}】内容质量不够，需要改进。

## 质量评审意见（必须逐条改进）
{last_review}

## 上一版数据
{json.dumps(data, ensure_ascii=False, indent=2)[:6000]}

## 要求
请根据评审意见逐条改进，重新生成完整的 JSON 数据。改进要点：
1. 对评语中指出不足的部分，必须大幅扩充内容
2. 之前达标的部分保持不变
3. 严格按 JSON Schema 格式输出，只输出 JSON

```json
{tp['data_schema']}
```"""
                    messages = [
                        {"role": "system", "content": tp['system']},
                        {"role": "user", "content": gen_prompt},
                    ]

                response = _run_async(self.llm_router.chat(messages))

                # 解析 JSON
                resp_str = response.strip()
                if "```json" in resp_str:
                    resp_str = resp_str.split("```json")[1].split("```")[0].strip()
                elif "```" in resp_str:
                    resp_str = resp_str.split("```")[1].split("```")[0].strip()

                data = json.loads(resp_str)

                # --- 代码级硬规则检查（先于LLM自评分，快速拦截低质量数据） ---
                hard_passed, hard_issues = self._check_deliverable_hard_rules(dtype, data)
                if not hard_passed:
                    logger.warning(f"Deliverable hard rules failed round {quality_round + 1}: {hard_issues}")
                    last_review = "### 代码质量检查未通过（以下问题必须修复）：\n"
                    for issue in hard_issues:
                        last_review += f"- {issue}\n"
                    # 硬规则不通过，直接进入下一轮迭代，跳过LLM自评分
                    continue
                else:
                    hard_rules_passed = True
                    logger.info(f"Deliverable hard rules passed round {quality_round + 1}")

                # --- LLM 自评分 ---
                data_preview = json.dumps(data, ensure_ascii=False, indent=2)[:8000]
                review_prompt = f"""你是一位严格的质量评审专家。请对以下【{tp['label']}】的内容质量进行评分。

## 质量标准
{tp['quality_requirements']}

## 待评审内容
{data_preview}

## 评分规则（满分10分）
请从以下维度评分：
1. **内容完整度**（0-3分）：所有字段是否都有实质性内容，有无空缺或占位符
2. **数据丰富度**（0-3分）：是否包含具体数据、统计值、案例等量化信息
3. **专业深度**（0-2分）：专业术语使用是否准确，论述是否深入
4. **格式规范**（0-2分）：JSON结构是否完整，字段类型是否正确

## 输出格式（严格按此格式，只输出JSON）
```json
{{"score": 8, "completeness": {{"score": 2, "issues": ["issue1"]}}, "richness": {{"score": 2, "issues": ["issue1"]}}, "depth": {{"score": 1, "issues": ["issue1"]}}, "format": {{"score": 2, "issues": []}}, "summary": "总体评价和改进建议", "improvements": ["具体改进建议1", "具体改进建议2"]}}
```"""

                review_messages = [
                    {"role": "system", "content": "你是一位严格的质量评审专家，请客观、严格地评分。只有真正高质量的内容才能获得高分。"},
                    {"role": "user", "content": review_prompt},
                ]
                review_response = _run_async(self.llm_router.chat(review_messages))

                # 解析评分
                review_str = review_response.strip()
                if "```json" in review_str:
                    review_str = review_str.split("```json")[1].split("```")[0].strip()
                elif "```" in review_str:
                    review_str = review_str.split("```")[1].split("```")[0].strip()

                try:
                    review_data = json.loads(review_str)
                    last_score = review_data.get("score", 0)
                    improvements = review_data.get("improvements", [])
                    summary = review_data.get("summary", "")

                    # 构建评审意见文本
                    last_review = f"### 评分：{last_score}/10\n"
                    if summary:
                        last_review += f"### 总体评价\n{summary}\n"
                    if improvements:
                        last_review += f"### 必须改进的问题\n"
                        for imp in improvements:
                            last_review += f"- {imp}\n"

                    logger.info(f"Deliverable quality round {quality_round + 1}: score={last_score}/10")

                    if last_score >= quality_pass_score:
                        logger.info(f"Deliverable passed quality check at round {quality_round + 1}")
                        break
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Quality review parse error: {e}, accepting current data")
                    break
            # ========== Loop 质量检验结束 ==========

            if data is None:
                logger.error(f"All quality rounds failed for {dtype}, no valid data")
                return None

            # 使用对应的导出器生成文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_goal = "".join(c if c.isalnum() or c in " _-" else "_" for c in goal[:30]).strip()
            filename = f"{dtype}_{safe_goal}_{timestamp}.{tp['format']}"
            filepath = os.path.join(output_dir, filename)

            # 动态导入导出器
            from medai.export import (
                PaperExporter, GrantProposalExporter, ProtocolExporter,
                ResponseLetterExporter, MetaAnalysisExporter, BudgetExporter,
                JournalDatabaseExporter, SurvivalDataExporter,
                ResearchPresentationExporter, ImagingTeachingExporter,
                BioinformaticsReportExporter
            )

            exporter_map = {
                'paper': PaperExporter,
                'grant': GrantProposalExporter,
                'protocol': ProtocolExporter,
                'meta_analysis': MetaAnalysisExporter,
                'budget': BudgetExporter,
                'survival': SurvivalDataExporter,
                'response_letter': ResponseLetterExporter,
                'research_report': ResearchPresentationExporter,
                'teaching': ImagingTeachingExporter,
                'bioinformatics': BioinformaticsReportExporter,
                'journal_db': JournalDatabaseExporter,
            }

            exporter_class = exporter_map.get(dtype)
            if exporter_class is None:
                logger.warning(f"No exporter for type: {dtype}")
                return None

            exporter = exporter_class()
            export_fn = getattr(exporter, tp['exporter_fn'])
            export_fn(data, filepath)

            logger.info(f"Deliverable generated: {filepath} (hard_rules={hard_rules_passed}, quality_score={last_score}/10)")

            return {
                'type': dtype,
                'label': tp.get('label', dtype),
                'format': tp['format'],
                'filename': filename,
                'filepath': filepath,
                'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                'quality_score': last_score,
                'hard_rules_passed': hard_rules_passed,
            }
        except json.JSONDecodeError as e:
            logger.error(f"Deliverable JSON parse error for {dtype}: {e}")
            return None
        except ImportError as e:
            logger.warning(f"Deliverable exporter import error for {dtype}: {e}")
            return None
        except Exception as e:
            logger.error(f"Deliverable generation error for {dtype}: {e}")
            return None
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用工具列表"""
        return self.tool_registry.list_tools()
    
    def get_registered_agents(self) -> List[Dict[str, str]]:
        """获取已注册的 Agent 列表"""
        return [
            {'name': name, 'role': agent.role}
            for name, agent in self.agent_orchestrator._agents.items()
        ]
    
    # === Skill 系统方法 ===
    
    def execute_skill(self, skill_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行已注册的 Skill
        
        Args:
            skill_name: Skill 名称
            arguments: Skill 参数字典
        
        Returns:
            Skill 执行结果字典
        """
        if arguments is None:
            arguments = {}
        
        logger.info(f"Executing skill: {skill_name}")
        try:
            result = _run_async(self.skill_executor.execute(skill_name, arguments))
            return {
                'success': result.success,
                'output': result.output,
                'duration_ms': result.duration_ms,
                'error': result.error,
                'skill_name': result.skill_name
            }
        except Exception as e:
            logger.error(f"Skill execution error: {e}")
            return {'success': False, 'error': str(e), 'skill_name': skill_name}
    
    def list_skills(self, tag: str = None, builtin_only: bool = False) -> List[Dict[str, Any]]:
        """列出所有可用 Skills
        
        Args:
            tag: 按标签过滤
            builtin_only: 仅显示内置 Skills
        
        Returns:
            Skill 列表
        """
        skills = self.skill_registry.list_skills(tag=tag, builtin_only=builtin_only)
        return [
            {
                'name': s.name,
                'description': s.description,
                'version': s.version,
                'tags': s.tags,
                'is_builtin': s.is_builtin,
                'usage_count': s.usage_count,
                'success_rate': round(s.success_rate, 2),
                'parameters': [
                    {'name': p.name, 'type': p.type, 'required': p.required, 'description': p.description}
                    for p in s.parameters
                ]
            }
            for s in skills
        ]
    
    def search_skills(self, query: str) -> List[Dict[str, Any]]:
        """搜索 Skills
        
        Args:
            query: 搜索关键词
        
        Returns:
            匹配的 Skill 列表
        """
        skills = self.skill_registry.search(query)
        return [{'name': s.name, 'description': s.description, 'tags': s.tags} for s in skills]
    
    def learn_skill_from_conversation(
        self,
        conversation: List[Dict[str, str]] = None,
        skill_name: str = None,
        auto_register: bool = True
    ) -> Dict[str, Any]:
        """从对话中学习并创建 Skill
        
        Args:
            conversation: 对话历史，如未提供则使用当前会话历史
            skill_name: Skill 名称
            auto_register: 是否自动注册到注册表
        
        Returns:
            学习结果
        """
        if conversation is None:
            conversation = self.memory.get_conversation_history()
        
        if not conversation:
            return {'success': False, 'error': '没有可用的对话历史'}
        
        try:
            skill = _run_async(
                self.skill_learner.learn_with_llm(conversation, skill_name)
            )
            
            if skill is None:
                # 回退到规则提取
                skill = self.skill_learner.learn_from_conversation(conversation, skill_name)
            
            if skill is None:
                return {'success': False, 'error': '未能从对话中提取到可复用的工作流'}
            
            if auto_register:
                self.skill_registry.register(skill)
            
            return {
                'success': True,
                'skill_name': skill.name,
                'description': skill.description,
                'steps_count': len(skill.steps),
                'parameters_count': len(skill.parameters),
                'tags': skill.tags,
                'registered': auto_register
            }
        except Exception as e:
            logger.error(f"Learn skill error: {e}")
            return {'success': False, 'error': str(e)}
    
    def suggest_learnable_skills(self) -> List[Dict[str, Any]]:
        """建议当前会话中可以提取 Skill 的对话片段
        
        Returns:
            建议列表，每项包含 confidence 和 preview
        """
        conversation = self.memory.get_conversation_history()
        if not conversation:
            return []
        
        suggestions = self.skill_learner.suggest_skills(conversation)
        return suggestions
    
    def register_custom_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """注册自定义 Skill
        
        Args:
            skill_data: Skill 数据字典，需包含 name, description, parameters, steps
        
        Returns:
            注册结果
        """
        try:
            from .skills.models import Skill, SkillStep, SkillParameter, StepType
            
            parameters = [
                SkillParameter(**p) for p in skill_data.get('parameters', [])
            ]
            steps = [
                SkillStep(
                    **{**s, 'step_type': StepType(s.get('step_type', 'llm_call'))}
                ) for s in skill_data.get('steps', [])
            ]
            
            skill = Skill(
                name=skill_data['name'],
                description=skill_data.get('description', ''),
                parameters=parameters,
                steps=steps,
                tags=skill_data.get('tags', ['custom']),
                is_builtin=False
            )
            
            self.skill_registry.register(skill)
            return {'success': True, 'skill_name': skill.name}
        except Exception as e:
            logger.error(f"Register custom skill error: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_skill(self, skill_name: str, file_path: str) -> bool:
        """导出 Skill 到文件
        
        Args:
            skill_name: Skill 名称
            file_path: 导出文件路径
        
        Returns:
            是否成功
        """
        return self.skill_registry.export_skill(skill_name, file_path)
    
    def import_skill(self, file_path: str) -> Dict[str, Any]:
        """从文件导入 Skill
        
        Args:
            file_path: 文件路径
        
        Returns:
            导入结果
        """
        try:
            skill = self.skill_registry.import_skill(file_path)
            return {'success': True, 'skill_name': skill.name}
        except Exception as e:
            return {'success': False, 'error': str(e)}
