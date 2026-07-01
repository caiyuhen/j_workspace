"""
MedAIagents 桌面应用后端服务
Desktop App Backend Server
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# FastAPI 相关
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import io

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


class SkillExecuteRequest(BaseModel):
    skill_name: str
    arguments: Dict[str, Any] = {}


class RCTRequest(BaseModel):
    intervention: str
    condition: str
    primary_endpoint: str
    sample_size: int = 100


class MetaAnalysisRequest(BaseModel):
    topic: str
    effect_measure: str = "OR"
    num_studies: int = 10
    language: str = "chinese"


class GrantRequest(BaseModel):
    title: str
    grant_type: str = "NSFC"
    research_area: str = ""
    budget: float = 50


class SurvivalRequest(BaseModel):
    data_description: str
    time_variable: str
    event_variable: str
    group_variable: str = ""
    covariates: str = ""


class LiteratureReviewRequest(BaseModel):
    topic: str
    num_papers: int = 30
    focus_areas: str = ""


class PlanRequest(BaseModel):
    task: str
    context: str = ""


class SandboxRequest(BaseModel):
    code: str
    language: str = "python"


class ExportRequest(BaseModel):
    export_type: str
    data: Dict[str, Any]
    format: str = "docx"


class ModelSwitchRequest(BaseModel):
    provider: str


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


# ==================== Skills API ====================

@app.get("/api/skills")
async def list_skills(tag: str = None, builtin_only: bool = False):
    """列出所有 Skills"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        skills = agent.list_skills(tag=tag, builtin_only=builtin_only)
        return {"success": True, "skills": skills, "count": len(skills)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/skills/execute")
async def execute_skill(request: SkillExecuteRequest):
    """执行 Skill"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        result = agent.execute_skill(request.skill_name, request.arguments)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/skills/search")
async def search_skills(query: str):
    """搜索 Skills"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        results = agent.search_skills(query)
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 科研工具 API ====================

@app.post("/api/research/rct")
async def rct_design(request: RCTRequest):
    """RCT 方案设计"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        result = agent.execute_skill('rct_protocol_design_workflow', {
            'intervention': request.intervention,
            'condition': request.condition,
            'primary_endpoint': request.primary_endpoint,
            'sample_size': request.sample_size
        })
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/research/meta-analysis")
async def meta_analysis(request: MetaAnalysisRequest):
    """Meta 分析写作"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        result = agent.execute_skill('meta_analysis_writing_workflow', {
            'topic': request.topic,
            'effect_measure': request.effect_measure,
            'num_studies': request.num_studies,
            'language': request.language
        })
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/research/grant")
async def grant_proposal(request: GrantRequest):
    """基金申请书"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        result = agent.execute_skill('grant_proposal_writing_workflow', {
            'title': request.title,
            'grant_type': request.grant_type,
            'research_area': request.research_area,
            'budget': request.budget
        })
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/research/survival")
async def survival_analysis(request: SurvivalRequest):
    """生存分析"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        result = agent.execute_skill('survival_analysis_workflow', {
            'data_description': request.data_description,
            'time_variable': request.time_variable,
            'event_variable': request.event_variable,
            'group_variable': request.group_variable,
            'covariates': request.covariates
        })
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/research/literature-review")
async def literature_review(request: LiteratureReviewRequest):
    """文献综述"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        result = agent.execute_skill('literature_review_workflow', {
            'topic': request.topic,
            'num_papers': request.num_papers,
            'focus_areas': request.focus_areas
        })
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 模型管理 API ====================

@app.get("/api/models")
async def list_models():
    """列出可用模型和当前配置"""
    try:
        config = Config()
        providers = config.get('llm.providers', {})
        default_provider = config.get('llm.default_provider', 'unknown')
        return {
            "success": True,
            "default_provider": default_provider,
            "providers": list(providers.keys()),
            "config": {k: {kk: vv for kk, vv in v.items() if kk != 'api_key'} for k, v in providers.items()}
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/models/switch")
async def switch_model(request: ModelSwitchRequest):
    """切换大模型"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        agent.switch_model(request.provider)
        return {"success": True, "provider": request.provider, "message": f"已切换到 {request.provider}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 任务规划 API ====================

@app.post("/api/plan")
async def plan_task(request: PlanRequest):
    """任务规划"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        result = agent.plan_and_execute(request.task, request.context)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 代码沙箱 API ====================

@app.post("/api/sandbox/execute")
async def sandbox_execute(request: SandboxRequest):
    """代码沙箱执行"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        result = agent.execute_code(request.code, language=request.language)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 导出 API ====================

@app.post("/api/export")
async def export_document(request: ExportRequest):
    """导出文档"""
    try:
        from medai.export import PaperExporter, GrantProposalExporter, ProtocolExporter, MetaAnalysisExporter
        
        exporters = {
            'paper': PaperExporter,
            'grant': GrantProposalExporter,
            'protocol': ProtocolExporter,
            'meta': MetaAnalysisExporter,
        }
        
        exporter_class = exporters.get(request.export_type)
        if not exporter_class:
            return {"success": False, "error": f"不支持的导出类型: {request.export_type}"}
        
        # 创建临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=f'.{request.format}', delete=False) as f:
            temp_path = f.name
        
        exporter = exporter_class()
        if request.export_type == 'paper':
            exporter.export(request.data, temp_path)
        elif request.export_type == 'grant':
            exporter.export(request.data, temp_path)
        
        # 读取文件内容返回
        with open(temp_path, 'rb') as f:
            content = f.read()
        os.unlink(temp_path)
        
        filename = f"export.{request.format}"
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 文件上传 API ====================

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """文件上传"""
    try:
        import tempfile
        upload_dir = os.path.join(tempfile.gettempdir(), "medai_uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "path": file_path,
            "message": "文件上传成功"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== Agent 编排 API ====================

@app.get("/api/agents")
async def list_agents():
    """列出注册 Agent"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        agents = agent.get_registered_agents()
        return {"success": True, "agents": agents}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/agents/orchestrate")
async def orchestrate_agents(request: Dict[str, Any]):
    """多 Agent 编排"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        task = request.get('task', '')
        mode = request.get('mode', 'auto')
        result = agent.auto_orchestrate(task) if mode == 'auto' else agent.delegate_to_agents(task)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8228)
