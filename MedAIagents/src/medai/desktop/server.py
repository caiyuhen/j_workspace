"""
MedAIagents 桌面应用后端服务
Desktop App Backend Server
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# FastAPI 相关
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from medai import MedicalAgent, Config
from medai.cdss import ClinicalDecisionSupport
from medai.knowledge import MedicalKnowledgeBase
from medai.emr import ICD10Coder, EMRNoteGenerator
from medai.security import SecurityManager


# Pydantic 模型
class ChatRequest(BaseModel):
    message: str
    use_knowledge: bool = True


class DiagnosisRequest(BaseModel):
    symptoms: List[str]
    lab_results: Optional[Dict[str, str]] = None


class MedicationRequest(BaseModel):
    medications: List[str]
    allergies: Optional[List[str]] = None
    doses: Optional[Dict[str, float]] = None


class NoteRequest(BaseModel):
    note_type: str
    patient_info: Dict[str, Any]
    clinical_data: Dict[str, Any]


class ICD10Request(BaseModel):
    diagnosis: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    use_pubmed: bool = False


# 初始化应用
app = FastAPI(title="MedAIagents Desktop API", version="1.0.0")

# 全局实例
agent: Optional[MedicalAgent] = None
cdss: Optional[ClinicalDecisionSupport] = None
kb: Optional[MedicalKnowledgeBase] = None
icd_coder: Optional[ICD10Coder] = None
note_generator: Optional[EMRNoteGenerator] = None
security: Optional[SecurityManager] = None


def initialize_services():
    """初始化所有服务"""
    global agent, cdss, kb, icd_coder, note_generator, security
    try:
        config = Config()
        agent = MedicalAgent(config)
        cdss = ClinicalDecisionSupport(config)
        kb = MedicalKnowledgeBase(config)
        icd_coder = ICD10Coder(config)
        note_generator = EMRNoteGenerator(config)
        security = SecurityManager(config)
        print("✅ 所有服务初始化成功")
    except Exception as e:
        print(f"⚠️  服务初始化警告: {e}")
        print("⚠️  部分功能可能需要配置 LLM API 密钥才能使用")


# 路由
@app.on_event("startup")
async def startup_event():
    """启动时初始化服务"""
    initialize_services()


@app.get("/", response_class=HTMLResponse)
async def root():
    """主页面"""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>MedAIagents 桌面应用</h1>"


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "agent": agent is not None,
            "cdss": cdss is not None,
            "knowledge_base": kb is not None,
            "icd_coder": icd_coder is not None,
            "note_generator": note_generator is not None
        }
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """聊天接口"""
    try:
        if agent is None:
            raise HTTPException(status_code=500, detail="Agent 未初始化")
        
        response = agent.chat(request.message, use_knowledge=request.use_knowledge)
        
        return {
            "success": True,
            "message": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"抱歉，处理您的请求时出现错误: {str(e)}",
            "error": str(e)
        }


@app.post("/api/diagnosis")
async def diagnosis(request: DiagnosisRequest):
    """诊断辅助"""
    try:
        if cdss is None:
            raise HTTPException(status_code=500, detail="CDSS 未初始化")
        
        result = cdss.diagnose(request.symptoms, request.lab_results or {})
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/medication-safety")
async def medication_safety(request: MedicationRequest):
    """用药安全检查"""
    try:
        if cdss is None:
            raise HTTPException(status_code=500, detail="CDSS 未初始化")
        
        result = cdss.check_medication_safety(
            request.medications,
            request.allergies or [],
            request.doses or {}
        )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/generate-note")
async def generate_note(request: NoteRequest):
    """生成医学文书"""
    try:
        if note_generator is None:
            raise HTTPException(status_code=500, detail="NoteGenerator 未初始化")
        
        note_content = agent.generate_medical_note(
            request.note_type,
            request.patient_info,
            request.clinical_data
        )
        
        return {
            "success": True,
            "content": note_content,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/icd10")
async def get_icd10(request: ICD10Request):
    """ICD-10 编码查询"""
    try:
        if icd_coder is None:
            raise HTTPException(status_code=500, detail="ICD10Coder 未初始化")
        
        result = icd_coder.get_icd10_code(request.diagnosis)
        
        return {
            "success": True,
            "diagnosis": request.diagnosis,
            "icd10_code": result,
            "found": result is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/search")
async def search_knowledge(request: SearchRequest):
    """知识库搜索"""
    try:
        if kb is None:
            raise HTTPException(status_code=500, detail="KnowledgeBase 未初始化")
        
        results = kb.search(request.query, request.limit, request.use_pubmed)
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/history")
async def get_history():
    """获取对话历史"""
    try:
        if agent is None:
            return {"success": False, "history": []}
        
        history = agent.get_conversation_history()
        
        return {
            "success": True,
            "history": history,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/audit-logs")
async def get_audit_logs(limit: int = 50):
    """获取审计日志"""
    try:
        if agent is None:
            logs = []
        else:
            logs = agent.get_audit_logs(limit)
        
        return {
            "success": True,
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    try:
        if agent is None:
            kb_stats = kb.get_statistics() if kb else {}
            return {
                "success": True,
                "stats": {
                    "version": "1.0.0",
                    "knowledge_base": kb_stats
                }
            }
        
        stats = agent.get_statistics()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8228)
