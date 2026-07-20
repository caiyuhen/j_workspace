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
from urllib.parse import quote

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


class ExportNoteRequest(BaseModel):
    content: str
    filename: str = ""


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
    """聊天接口（支持自动任务规划）"""
    try:
        if agent is None:
            raise HTTPException(status_code=500, detail="Agent 未初始化")
        
        result = agent.chat_with_auto_plan(request.message, use_knowledge=request.use_knowledge)
        
        response_data = {
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
        
        if result["type"] == "plan":
            # 复杂任务：返回规划结果
            response_data["message"] = result["message"]
            response_data["type"] = "plan"
            response_data["plan"] = result["plan"]
            response_data["deliverables"] = result.get("deliverables", [])
        else:
            # 简单对话：直接返回
            response_data["message"] = result["message"]
            response_data["type"] = "simple"
        
        return response_data
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


@app.post("/api/export-note")
async def export_note(request: ExportNoteRequest):
    """导出医学文书为文本文件（绕过前端下载触发桌面环境异常）"""
    try:
        content = request.content
        if not content:
            raise HTTPException(status_code=400, detail="内容为空")
        
        filename = request.filename or f"医学文书_{datetime.now().strftime('%Y%m%d')}.txt"
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # 使用 UTF-8 编码
        encoded_filename = quote(filename)
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


# ==================== 知识库管理 API ====================

@app.post("/api/knowledge/upload")
async def knowledge_upload(file: UploadFile = File(...), category: str = "上传文档"):
    """上传文件并索引到本地知识库（支持 PDF/DOCX/TXT/MD）"""
    try:
        if kb is None:
            return {"success": False, "error": "KnowledgeBase 未初始化"}
        
        # 保存到临时目录
        upload_dir = os.path.join(tempfile.gettempdir(), "medai_uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 解析并索引
        result = kb.index_file(file_path, category=category)
        
        return {
            "success": result.get("success", False),
            "message": result.get("message") or result.get("error", ""),
            "filename": file.filename,
            "size": len(content),
            "chunk_count": result.get("chunk_count", 0),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/knowledge/documents")
async def knowledge_documents(limit: int = 100, offset: int = 0):
    """列出已索引到本地知识库的文档"""
    try:
        if kb is None:
            return {"success": False, "error": "KnowledgeBase 未初始化"}
        
        docs = kb.list_uploaded_documents(limit=limit, offset=offset)
        return {
            "success": True,
            "documents": docs,
            "count": len(docs),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.delete("/api/knowledge/documents/{doc_id}")
async def knowledge_delete_document(doc_id: int):
    """删除本地知识库中的指定文档"""
    try:
        if kb is None:
            return {"success": False, "error": "KnowledgeBase 未初始化"}
        
        deleted = kb.delete_uploaded_document(doc_id)
        return {
            "success": deleted,
            "message": "已删除" if deleted else "未找到该文档",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class IMAConfigRequest(BaseModel):
    client_id: str
    api_key: str


class IMASearchKBRequest(BaseModel):
    query: str = ""
    limit: int = 20


class IMASearchRequest(BaseModel):
    query: str
    knowledge_base_id: str


class IMAListContentsRequest(BaseModel):
    knowledge_base_id: str
    folder_id: str = ""


@app.post("/api/knowledge/ima/config")
async def ima_configure(request: IMAConfigRequest):
    """配置 IMA 知识库连接（ClientID + APIKey）"""
    try:
        if kb is None:
            return {"success": False, "error": "KnowledgeBase 未初始化"}
        
        kb.configure_ima(request.client_id.strip(), request.api_key.strip())
        return {
            "success": True,
            "message": "IMA 配置已保存",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/knowledge/ima/status")
async def ima_status():
    """获取 IMA 配置状态"""
    try:
        if kb is None:
            return {"success": False, "configured": False, "error": "KnowledgeBase 未初始化"}
        
        client = kb.get_ima_client()
        return {
            "success": True,
            "configured": client is not None,
        }
    except Exception as e:
        return {"success": False, "configured": False, "error": str(e)}


@app.post("/api/knowledge/ima/search-kb")
async def ima_search_kb(request: IMASearchKBRequest):
    """搜索/列出 IMA 知识库"""
    try:
        if kb is None:
            return {"success": False, "error": "KnowledgeBase 未初始化"}
        
        result = await kb.search_ima_knowledge_bases(request.query, request.limit)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/knowledge/ima/search")
async def ima_search(request: IMASearchRequest):
    """在 IMA 知识库中搜索文件"""
    try:
        if kb is None:
            return {"success": False, "error": "KnowledgeBase 未初始化"}
        
        result = await kb.search_ima_knowledge(request.query, request.knowledge_base_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/knowledge/ima/contents")
async def ima_contents(request: IMAListContentsRequest):
    """浏览 IMA 知识库中的文件和文件夹"""
    try:
        if kb is None:
            return {"success": False, "error": "KnowledgeBase 未初始化"}
        
        result = await kb.list_ima_knowledge_contents(request.knowledge_base_id, request.folder_id)
        return result
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
        
        # 构建可用模型列表
        all_models = []
        for provider_name, provider_config in providers.items():
            available = provider_config.get('available_models', [])
            current_model = provider_config.get('default_model', '')
            for m in available:
                all_models.append({
                    "id": m.get('id', ''),
                    "name": m.get('name', m.get('id', '')),
                    "description": m.get('description', ''),
                    "provider": provider_name,
                    "is_current": m.get('id', '') == current_model
                })
        
        return {
            "success": True,
            "default_provider": default_provider,
            "providers": list(providers.keys()),
            "models": all_models,
            "current_model": providers.get(default_provider, {}).get('default_model', '')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/models/switch")
async def switch_model(request: ModelSwitchRequest):
    """切换模型提供商"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        agent.switch_model(request.provider)
        return {"success": True, "provider": request.provider, "message": f"已切换到 {request.provider}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class ModelSwitchIdRequest(BaseModel):
    model_id: str
    provider: str = None


@app.post("/api/models/switch-model")
async def switch_model_id(request: ModelSwitchIdRequest):
    """切换具体模型 ID（在同一 provider 内切换不同模型）"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        
        config = Config()
        provider = request.provider or config.get('llm.default_provider', 'cherryin')
        provider_config = config.get(f'llm.providers.{provider}', {})
        
        # 检查模型是否在可用列表中
        available = provider_config.get('available_models', [])
        model_ids = [m.get('id') for m in available]
        if request.model_id not in model_ids:
            return {"success": False, "error": f"模型 {request.model_id} 不在可用列表中"}
        
        # 更新配置中的 default_model
        config.set(f'llm.providers.{provider}.default_model', request.model_id)
        
        # 重新初始化 LLM router（让它读取新的配置）
        agent.llm_router.switch_provider(provider)
        
        return {
            "success": True,
            "provider": provider,
            "model_id": request.model_id,
            "message": f"已切换到模型: {request.model_id}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class AddProviderRequest(BaseModel):
    name: str
    api_key: str
    base_url: str
    default_model: str = ""
    temperature: float = 0.3
    max_tokens: int = 4096
    description: str = ""


class TestProviderRequest(BaseModel):
    provider: str


class DeleteProviderRequest(BaseModel):
    provider: str


@app.get("/api/providers")
async def list_providers():
    """列出所有 Provider（含模型数量和连接状态概要）"""
    try:
        config = Config()
        providers = config.get('llm.providers', {})
        default_provider = config.get('llm.default_provider', '')
        
        result = []
        for name, pconf in providers.items():
            api_key = pconf.get('api_key', '')
            masked_key = (api_key[:8] + '...') if len(api_key) > 8 else ('***' if api_key else '未配置')
            models = pconf.get('available_models', [])
            result.append({
                "name": name,
                "base_url": pconf.get('base_url', ''),
                "default_model": pconf.get('default_model', ''),
                "api_key_masked": masked_key,
                "has_api_key": bool(api_key and not api_key.startswith('${')),
                "temperature": pconf.get('temperature', 0.3),
                "max_tokens": pconf.get('max_tokens', 4096),
                "model_count": len(models),
                "is_default": name == default_provider,
            })
        
        return {"success": True, "default_provider": default_provider, "providers": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/providers/add")
async def add_provider(request: AddProviderRequest):
    """添加新的 Provider 并持久化到 config.yaml"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        
        name = request.name.strip().lower()
        if not name:
            return {"success": False, "error": "Provider 名称不能为空"}
        if not name.isidentifier():
            return {"success": False, "error": "Provider 名称只能包含英文字母、数字和下划线"}
        
        config = Config()
        existing = config.get(f'llm.providers.{name}')
        if existing:
            return {"success": False, "error": f"Provider '{name}' 已存在，请使用其他名称"}
        
        # 构建配置
        provider_config = {
            'api_key': request.api_key.strip(),
            'base_url': request.base_url.strip().rstrip('/'),
            'default_model': request.default_model.strip(),
            'temperature': request.temperature,
            'max_tokens': request.max_tokens,
            'available_models': [],
        }
        if request.description:
            provider_config['description'] = request.description
        
        # 写入内存配置
        config.set(f'llm.providers.{name}', provider_config)
        
        # 动态注册到 LLM Router（会创建 SDK 实例）
        agent.llm_router.register_provider(name, provider_config)
        
        # 持久化到 config.yaml
        config.save()
        
        return {
            "success": True,
            "provider": name,
            "message": f"Provider '{name}' 添加成功"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/providers/test")
async def test_provider(request: TestProviderRequest):
    """测试 Provider 连接"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        
        result = await agent.llm_router.test_provider_connection(request.provider)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/providers/delete")
async def delete_provider(request: DeleteProviderRequest):
    """删除 Provider 并持久化到 config.yaml"""
    try:
        if agent is None:
            return {"success": False, "error": "Agent 未初始化"}
        
        name = request.provider.strip()
        config = Config()
        
        # 从 LLM Router 中移除
        agent.llm_router.remove_provider(name)
        
        # 从配置中删除
        config.delete(f'llm.providers.{name}')
        
        # 持久化到 config.yaml
        config.save()
        
        return {
            "success": True,
            "provider": name,
            "message": f"Provider '{name}' 已删除"
        }
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
        from medai.export import (
            PaperExporter, GrantProposalExporter, ProtocolExporter,
            ResponseLetterExporter, MetaAnalysisExporter, BudgetExporter,
            JournalDatabaseExporter, SurvivalDataExporter,
            ResearchPresentationExporter, ImagingTeachingExporter,
            BioinformaticsReportExporter
        )
        
        exporter_map = {
            'paper': (PaperExporter, 'export_paper'),
            'grant': (GrantProposalExporter, 'export_proposal'),
            'protocol': (ProtocolExporter, 'export_protocol'),
            'response_letter': (ResponseLetterExporter, 'export_response_letter'),
            'meta_analysis': (MetaAnalysisExporter, 'export_meta_analysis'),
            'budget': (BudgetExporter, 'export_budget'),
            'journal_db': (JournalDatabaseExporter, 'export_journals'),
            'survival': (SurvivalDataExporter, 'export_survival_data'),
            'research_report': (ResearchPresentationExporter, 'export_research_report'),
            'teaching': (ImagingTeachingExporter, 'export_teaching'),
            'bioinformatics': (BioinformaticsReportExporter, 'export_bioinformatics_report'),
        }
        
        entry = exporter_map.get(request.export_type)
        if not entry:
            return {"success": False, "error": f"不支持的导出类型: {request.export_type}"}
        
        exporter_class, export_fn_name = entry
        
        # 创建临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=f'.{request.format}', delete=False) as f:
            temp_path = f.name
        
        exporter = exporter_class()
        export_fn = getattr(exporter, export_fn_name)
        export_fn(request.data, temp_path)
        
        # 读取文件内容返回
        with open(temp_path, 'rb') as f:
            content = f.read()
        os.unlink(temp_path)
        filename = f"export.{request.format}"
        encoded_filename = quote(filename, safe='')
        media_type_map = {
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type_map.get(request.format, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 文件下载 API ====================

@app.get("/api/download/{filename:path}")
async def download_file(filename: str):
    """下载存储在 data/exports 目录的自动生成文件"""
    try:
        import os
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'exports', filename)
        # 安全检查：防止路径穿越
        real_path = os.path.realpath(filepath)
        exports_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'exports'))
        if not real_path.startswith(exports_dir):
            return {"success": False, "error": "非法文件路径"}
        
        if not os.path.exists(real_path):
            return {"success": False, "error": f"文件不存在: {filename}"}
        
        with open(real_path, 'rb') as f:
            content = f.read()
        
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else 'bin'
        media_type_map = {
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf': 'application/pdf',
        }
        encoded_filename = quote(filename, safe='')
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type_map.get(ext, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/exports")
async def list_exports():
    """列出所有已生成的交付物文件"""
    try:
        import os
        exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        files = []
        for fname in os.listdir(exports_dir):
            fpath = os.path.join(exports_dir, fname)
            if os.path.isfile(fpath) and not fname.startswith('.'):
                files.append({
                    'filename': fname,
                    'size': os.path.getsize(fpath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                })
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: x['modified'], reverse=True)
        return {"success": True, "files": files}
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

# ==================== 包管理 API ====================

class PackageInstallRequest(BaseModel):
    package_name: str
    version: str = ""
    dry_run: bool = False


@app.post("/api/packages/install")
async def api_install_package(request: PackageInstallRequest):
    """安装 Python 包"""
    try:
        from medai.tools.system_tools import install_package
        result = install_package(request.package_name, version=request.version, dry_run=request.dry_run)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/packages/check")
async def api_check_package(request: PackageInstallRequest):
    """检查包安全性"""
    try:
        from medai.tools.system_tools import check_package
        result = check_package(request.package_name)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/packages")
async def api_list_packages(filter: str = ""):
    """列出已安装的包"""
    try:
        from medai.tools.system_tools import list_packages
        result = list_packages(filter)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


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
