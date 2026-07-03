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
    
    def _generate_deliverable(self, dtype: str, goal: str, subtasks: Dict[str, Any], output_dir: str) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成交付物数据并导出为文件
        
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
            subtasks_summary = json.dumps(subtasks, ensure_ascii=False, indent=2)[:3000]
            
            # 根据不同类型构建不同的生成提示
            type_prompts = {
                'paper': {
                    'exporter_fn': 'export_paper',
                    'exporter_class': 'PaperExporter',
                    'format': 'docx',
                    'label': '医学论文',
                    'system': '你是一个医学论文写作专家。请根据任务目标和执行结果，生成IMRaD结构的论文数据。',
                    'data_schema': '{"title": "论文标题", "authors": "作者（字符串）", "abstract": "摘要", "keywords": ["关键词"], "introduction": "引言", "methods": "方法", "results": "结果", "discussion": "讨论", "conclusion": "结论", "references": ["参考文献列表"]}'
                },
                'grant': {
                    'exporter_fn': 'export_proposal',
                    'exporter_class': 'GrantProposalExporter',
                    'format': 'docx',
                    'label': '基金申请书',
                    'system': '你是一个基金申请书撰写专家。请根据任务目标和执行结果，生成基金申请书的结构化数据。',
                    'data_schema': '{"title": "项目名称", "grant_type": "申请类型", "research_area": "研究领域", "applicant": "申请人", "institution": "依托单位", "rationale": "立项依据", "research_content": "研究内容", "objectives": "研究目标", "key_problems": "关键科学问题", "methodology": "研究方案", "feasibility": "可行性分析", "innovation": "创新点", "timeline": "年度计划", "expected_outcomes": "预期成果", "budget": {"total": 50, "items": [{"name": "设备费", "amount": 10, "notes": ""}]}}'
                },
                'protocol': {
                    'exporter_fn': 'export_protocol',
                    'exporter_class': 'ProtocolExporter',
                    'format': 'docx',
                    'label': '临床试验方案',
                    'system': '你是一个临床试验方案设计专家。请根据任务目标和执行结果，生成RCT试验方案的数据。',
                    'data_schema': '{"study_info": {"title": "方案标题", "study_type": "RCT", "phase": "III期", "indication": "适应症", "duration_months": 24}, "study_objectives": {"primary": "主要目的"}, "endpoints": {"primary": "主要终点"}, "inclusion_criteria": ["入选标准"], "exclusion_criteria": ["排除标准"], "sample_size": "样本量计算", "statistical_analysis": "统计方法", "ethical_considerations": {"informed_consent": "知情同意"}}'
                },
                'meta_analysis': {
                    'exporter_fn': 'export_meta_analysis',
                    'exporter_class': 'MetaAnalysisExporter',
                    'format': 'xlsx',
                    'label': 'Meta分析结果表',
                    'system': '你是一个Meta分析专家。请根据任务目标和执行结果，生成Meta分析的结构化数据（含各研究数据、汇总统计等）。',
                    'data_schema': '{"studies": [{"name": "研究1", "a_events": 50, "a_total": 100, "b_events": 30, "b_total": 100, "effect_size": 1.5}], "pooled_effect": 1.35, "ci_lower": 1.1, "ci_upper": 1.6, "i_squared": "45%", "q_statistic": 12.3, "p_value": "<0.01", "model": "Random"}'
                },
                'budget': {
                    'exporter_fn': 'export_budget',
                    'exporter_class': 'BudgetExporter',
                    'format': 'xlsx',
                    'label': '经费预算表',
                    'system': '你是一个科研经费预算专家。请根据任务目标和执行结果，生成经费预算表数据。',
                    'data_schema': '{"title": "经费预算标题", "total": 50, "items": [{"name": "科目名称", "amount": 10, "notes": "说明"}]}'
                },
                'survival': {
                    'exporter_fn': 'export_survival_data',
                    'exporter_class': 'SurvivalDataExporter',
                    'format': 'xlsx',
                    'label': '生存分析数据',
                    'system': '你是一个生存分析专家。请根据任务目标和执行结果，生成生存分析数据（每条记录含time, event, group等字段）。',
                    'data_schema': '[{"patient_id": "P001", "time": 12, "event": 1, "group": "治疗组", "age": 55, "stage": "III"}, {"patient_id": "P002", "time": 8, "event": 0, "group": "对照组", "age": 62, "stage": "IV"}]'
                },
                'response_letter': {
                    'exporter_fn': 'export_response_letter',
                    'exporter_class': 'ResponseLetterExporter',
                    'format': 'docx',
                    'label': '审稿回复信',
                    'system': '你是一个学术回复信撰写专家。请根据任务目标和执行结果，生成Response Letter的结构化数据。',
                    'data_schema': '{"manuscript_id": "MS-2024-001", "title": "文章标题", "authors": "作者列表", "responses": [{"comment": "审稿人意见", "response": "作者回复", "changes": "修改说明"}]}'
                },
                'research_report': {
                    'exporter_fn': 'export_research_report',
                    'exporter_class': 'ResearchPresentationExporter',
                    'format': 'pptx',
                    'label': '科研汇报PPT',
                    'system': '你是一个科研汇报PPT制作专家。请根据任务目标和执行结果，生成科研汇报演示文稿的数据。',
                    'data_schema': '{"title": "报告标题", "subtitle": "副标题", "background": ["背景1"], "methods": ["方法1"], "results": ["结果1"], "discussion": ["讨论1"], "conclusions": ["结论1"], "acknowledgments": ["致谢"]}'
                },
                'teaching': {
                    'exporter_fn': 'export_teaching',
                    'exporter_class': 'ImagingTeachingExporter',
                    'format': 'pptx',
                    'label': '影像教学PPT',
                    'system': '你是一个医学影像教学专家。请根据任务目标和执行结果，生成影像征象教学PPT的数据。',
                    'data_schema': '[{"name": "征象名称", "description": "描述", "modalities": ["CT"], "anatomy": ["解剖位置"], "diseases": ["相关疾病"], "severity": "严重程度"}]'
                },
                'bioinformatics': {
                    'exporter_fn': 'export_bioinformatics_report',
                    'exporter_class': 'BioinformaticsReportExporter',
                    'format': 'pptx',
                    'label': '生信分析报告PPT',
                    'system': '你是一个生物信息学分析专家。请根据任务目标和执行结果，生成生信分析报告PPT的数据。',
                    'data_schema': '{"title": "报告标题", "subtitle": "副标题", "sample_info": ["样本信息"], "mutation_summary": ["突变图谱"], "pathways": ["通路富集"], "survival": ["生存分析"], "conclusions": ["结论"]}'
                },
                'journal_db': {
                    'exporter_fn': 'export_journals',
                    'exporter_class': 'JournalDatabaseExporter',
                    'format': 'xlsx',
                    'label': '期刊数据库',
                    'system': '你是一个医学期刊数据库管理员。请根据任务目标生成相关期刊列表数据。',
                    'data_schema': '[{"name": "期刊名称", "impact_factor": 5.0, "jcr_quartile": "Q1", "cas_quartile": "Q1", "field": "领域", "oa_policy": "混合OA", "review_period": "3个月"}]'
                }
            }
            
            if dtype not in type_prompts:
                logger.warning(f"Unknown deliverable type: {dtype}")
                return None
            
            tp = type_prompts[dtype]
            
            # 调用 LLM 生成结构化数据
            prompt = f"""根据以下任务目标和子任务执行结果，生成{dtype}类型的结构化导出数据。

## 任务目标
{goal}

## 子任务执行结果
{subtasks_summary}

## 输出要求
请严格按照以下 JSON Schema 格式输出数据，不要包含其他内容：

```json
{tp['data_schema']}
```"""
            
            messages = [
                {"role": "system", "content": tp['system']},
                {"role": "user", "content": prompt},
            ]
            response = _run_async(self.llm_router.chat(messages))
            
            # 解析 JSON
            resp_str = response.strip()
            if "```json" in resp_str:
                resp_str = resp_str.split("```json")[1].split("```")[0].strip()
            elif "```" in resp_str:
                resp_str = resp_str.split("```")[1].split("```")[0].strip()
            
            data = json.loads(resp_str)
            
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
            
            if dtype in ('meta_analysis', 'budget', 'survival') or dtype == 'journal_db' or dtype == 'teaching':
                if dtype == 'meta_analysis':
                    export_fn(data, filepath)
                elif dtype == 'budget':
                    export_fn(data, filepath)
                elif dtype == 'survival':
                    export_fn(data, filepath)
                elif dtype == 'journal_db':
                    export_fn(data, filepath)
                elif dtype == 'teaching':
                    export_fn(data, filepath)
                else:
                    export_fn(data, filepath)
            else:
                export_fn(data, filepath)
            
            logger.info(f"Deliverable generated: {filepath}")
            
            return {
                'type': dtype,
                'label': tp.get('label', dtype),
                'format': tp['format'],
                'filename': filename,
                'filepath': filepath,
                'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
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
