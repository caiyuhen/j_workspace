"""
诊断代理

临床诊断辅助专家，提供：
- 病历分析
- 诊断建议
- 鉴别诊断
- 用药建议
- 风险评估
"""
from typing import Dict, List
from app.agents.base import BaseAgent, TaskContext, TaskResult


class DiagnosisAgent(BaseAgent):
    """
    诊断代理 - 临床诊断辅助专家
    
    通过调用大模型服务(192.168.0.214:8802/chat/)获取RAG增强的诊断建议。
    大模型内置的RAG会自动检索相关医学知识增强生成效果。
    """
    
    name = "诊断代理"
    display_name = "诊断代理"
    type = "diagnosis"
    description = "临床诊断辅助代理，提供病历分析和诊断建议"
    capabilities = [
        "medical_record_analysis",
        "diagnosis_suggestion", 
        "differential_diagnosis",
        "medication_advice",
        "risk_assessment"
    ]
    
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        执行诊断任务
        
        根据任务类型调用不同的处理方法
        """
        task_type = context.metadata.get("task_type", "diagnosis_suggestion")
        
        handlers = {
            "medical_record_analysis": self._analyze_record,
            "diagnosis_suggestion": self._suggest_diagnosis,
            "differential_diagnosis": self._differential_diagnosis,
            "medication_advice": self._medication_advice,
            "risk_assessment": self._risk_assessment
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
    
    async def _analyze_record(self, context: TaskContext) -> TaskResult:
        """
        分析病历
        
        解析病历文本，提取关键信息，生成结构化病历摘要。
        大模型RAG会自动检索相关医学知识辅助分析。
        """
        record = context.input.get("record", "") if isinstance(context.input, dict) else str(context.input)
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位资深临床医生，擅长病历分析。请分析病历并提取以下信息：

1. 主诉 (chief_complaint)
2. 现病史 (present_illness)
3. 既往史 (past_history)
4. 体格检查 (physical_examination)
5. 辅助检查 (auxiliary_examination)
6. 初步诊断 (preliminary_diagnosis)
7. 关键症状列表 (key_symptoms)

请以JSON格式返回结构化结果。"""
            },
            {"role": "user", "content": f"请分析以下病历：\n\n{record}"}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _suggest_diagnosis(self, context: TaskContext) -> TaskResult:
        """
        诊断建议
        
        根据症状和病史给出诊断建议。
        大模型RAG会自动检索相关疾病知识和临床指南。
        """
        input_data = context.input if isinstance(context.input, dict) else {"symptoms": str(context.input)}
        symptoms = input_data.get("symptoms", [])
        history = input_data.get("history", {})
        
        prompt_parts = []
        
        if symptoms:
            prompt_parts.append(f"症状: {symptoms}")
        if history:
            prompt_parts.append(f"病史: {history}")
        
        if not prompt_parts:
            prompt_parts.append(f"患者描述: {context.input}")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位资深临床医生，擅长诊断推理。请根据患者信息给出诊断建议：

1. 最可能的诊断及依据
2. 建议的检查项目
3. 需要警惕的危险信号
4. 紧急程度评估(urgent/emergency/routine)
5. 建议就诊科室

请以JSON格式返回结果。注意：你的诊断仅供参考，不能替代医生的专业诊断。"""
            },
            {"role": "user", "content": "\n".join(prompt_parts)}
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _differential_diagnosis(self, context: TaskContext) -> TaskResult:
        """
        鉴别诊断
        
        提供鉴别诊断列表，帮助排除相似疾病。
        """
        input_data = context.input if isinstance(context.input, dict) else {"diagnosis": str(context.input)}
        primary_diagnosis = input_data.get("diagnosis", "")
        symptoms = input_data.get("symptoms", [])
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位资深临床医生，擅长鉴别诊断。请提供鉴别诊断列表：

对于每个鉴别诊断，请说明：
1. 疾病名称
2. 支持点
3. 不支持点
4. 需要做的鉴别检查

请以JSON数组格式返回结果。"""
            },
            {
                "role": "user", 
                "content": f"初步诊断: {primary_diagnosis}\n症状: {symptoms}\n\n请给出鉴别诊断。"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _medication_advice(self, context: TaskContext) -> TaskResult:
        """
        用药建议
        
        根据诊断结果提供用药方案建议。
        大模型RAG会自动检索药物信息和相互作用。
        """
        input_data = context.input if isinstance(context.input, dict) else {"diagnosis": str(context.input)}
        diagnosis = input_data.get("diagnosis", "")
        patient_info = input_data.get("patient_info", {})
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位资深临床医生和药师。请提供用药建议：

1. 推荐药物及用法用量
2. 药物作用机制
3. 注意事项
4. 可能的副作用
5. 药物相互作用
6. 特殊人群用药注意

请以JSON格式返回结果。注意：用药建议仅供参考，具体用药请遵医嘱。"""
            },
            {
                "role": "user",
                "content": f"诊断: {diagnosis}\n患者信息: {patient_info}\n\n请给出用药建议。"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
    
    async def _risk_assessment(self, context: TaskContext) -> TaskResult:
        """
        风险评估
        
        评估患者风险等级。
        """
        input_data = context.input if isinstance(context.input, dict) else {"patient_info": str(context.input)}
        patient_info = input_data.get("patient_info", {})
        diagnosis = input_data.get("diagnosis", "")
        
        response = await self.call_llm([
            {
                "role": "system",
                "content": """你是一位资深临床医生，擅长风险评估。请评估患者风险：

1. 风险等级(low/medium/high/critical)
2. 风险因素列表
3. 预后评估
4. 需要监测的指标
5. 随访建议

请以JSON格式返回结果。"""
            },
            {
                "role": "user",
                "content": f"患者信息: {patient_info}\n诊断: {diagnosis}\n\n请进行风险评估。"
            }
        ])
        
        return TaskResult(
            task_id=context.task_id,
            success=True,
            output=response
        )
