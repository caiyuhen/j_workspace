import requests
import logging
import json
import urllib3

# 禁用未验证的 HTTPS 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# 大模型后端实际暴露的 API 接口地址
LLM_URL = "http://192.168.0.126:8802/chat"
CHAT_HISTORY_DB = {}

def get_clinical_diagnosis(patient_id: str, prompt: str, twin_context: dict) -> dict:
    """
    大模型 Agent 中枢：负责多轮对话与意图理解，并结合 RAG 检索指南
    """
    system_prompt = (
        f"你是一名专业、权威的数字孪生医疗专家。当前患者：{twin_context.get('name', '未知')}，"
        f"既往病史：{', '.join(twin_context.get('history', []))}。\n"
        f"【实时生理数据】空腹血糖: {twin_context.get('fbg', '--')} mmol/L, 收缩压: {twin_context.get('sbp', '--')} mmHg。\n"
        f"【系统风险评估】{twin_context.get('risk_level', '--')}。\n"
        f"请直接回答患者的问题，给出专业的临床治疗方案建议。禁止使用通用的寒暄语，必须给出实质性的医疗指导（不少于150字）。"
    )
    
    combined_prompt = f"{system_prompt}\n\n患者最新主诉：\n“{prompt}”\n\n请针对上述“最新主诉”进行详细的病理分析和下一步治疗方案推荐："

    payload = {
        "prompt": combined_prompt,
        "use_rag": True,
        "use_adapter": True,
        "history": [],
        "temperature": 0.5,
        "max_new_tokens": 1024
    }
    
    try:
        resp = requests.post(LLM_URL, json=payload, verify=False, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        reply_text = data.get("response", "")
        
        # 移除模型回复中可能附带的“注：”或“（注：”等后续免责说明内容
        import re
        reply_text = re.sub(r'[\(（]?注[:：].*', '', reply_text, flags=re.DOTALL)
        # 移除“——依据《...》制定”等内容
        reply_text = re.sub(r'——依据.*', '', reply_text, flags=re.DOTALL)
        
        # 移除可能存在的 Markdown 代码块标记 (例如 ```html, ```markdown, ``` 等)
        reply_text = re.sub(r'```[a-zA-Z]*\n', '', reply_text)
        reply_text = re.sub(r'```', '', reply_text)
        
        reply_text = reply_text.strip()
        
        # 兜底：如果模型没有返回有效文本，使用内置模板
        if not reply_text or not reply_text.strip():
            reply_text = f"根据您的各项指标和主诉（{prompt}），建议继续保持目前的治疗方案，定期复查。若有不适请及时就医。"

        return {
            "reply": reply_text,
            "retrieved_knowledge": data.get("retrieved_knowledge", []),
            "analysis": data.get("analysis", {})
        }
    except Exception as e:
        logger.error(f"LLM 接口调用失败: {e}")
        # 移除拦截兜底，直接返回报错信息，方便调试
        error_msg = f"大模型接口调用失败: {str(e)}"
        return {
            "reply": error_msg,
            "retrieved_knowledge": [],
            "analysis": {"intent": "fallback"}
        }

def generate_clinical_suggestion(prompt: str, use_rag: bool = True) -> dict:
    payload = {
        "prompt": prompt,
        "use_rag": use_rag,
        "use_adapter": True,
        "temperature": 0.2,
        "max_new_tokens": 1024
    }
    try:
        # clinical 建议也可以直接调用 /clinical 接口
        resp = requests.post(LLM_URL.replace("/chat", "/clinical"), json=payload, verify=False, timeout=180)
        resp.raise_for_status()
        data = resp.json()
            
        return {
            "response": data.get("response", ""),
            "retrieved_knowledge": data.get("retrieved_knowledge", [])
        }
    except Exception as e:
        logger.error(f"LLM 接口调用失败 (Clinical Suggestion): {e}")
        return {
            "response": f"大模型接口调用失败: {str(e)}",
            "retrieved_knowledge": []
        }
