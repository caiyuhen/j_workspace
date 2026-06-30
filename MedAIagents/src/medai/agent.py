"""
医学AI代理核心类
Medical AI Agent Core Class
"""

import asyncio
from typing import Dict, List, Any, Optional, Generator
from loguru import logger

from .config import Config
from .llm.routing import LLMRouter
from .memory.system import MemorySystem
from .knowledge.base import MedicalKnowledgeBase
from .cdss.diagnosis import ClinicalDecisionSupport
from .emr.automation import EMRNoteGenerator, ICD10Coder
from .security.compliance import SecurityManager


class MedicalAgent:
    """医学AI代理核心类"""
    
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
        
        # 会话信息
        self.current_user_id = kwargs.get('user_id', 'default')
        self.current_session_id = self.memory.create_session()
        
        # 系统提示词
        self.system_prompt = self._build_system_prompt()
        
        logger.info(f"MedicalAgent initialized - Session: {self.current_session_id}")
    
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
            response = asyncio.run(self.llm_router.chat(messages))
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
            'version': '1.0.0',
            'current_session': self.current_session_id,
            'messages_in_session': len(self.memory.session_messages),
            'knowledge_base_size': self.knowledge_base.get_statistics(),
            'total_sessions': len(self.list_sessions())
        }
