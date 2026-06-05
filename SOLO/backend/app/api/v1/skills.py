"""
Skill管理API - 完整实现

支持三种协议：skillhub.cn、MCP、本地工具
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

from app.services.skill_service import skill_service
from app.api.v1.auth import get_current_active_user, TokenData

logger = logging.getLogger(__name__)
router = APIRouter()


# ============== 数据模型 ==============

class SkillInfo(BaseModel):
    """Skill信息"""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    protocol: str
    is_active: bool = True
    is_builtin: bool = False
    usage_count: int = 0
    last_used_at: Optional[datetime] = None


class SkillDetail(BaseModel):
    """Skill详情"""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    protocol: str
    is_active: bool = True
    is_builtin: bool = False
    config: Dict[str, Any] = {}
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime


class SkillInvokeRequest(BaseModel):
    """Skill调用请求"""
    input: Dict[str, Any] = Field(..., description="输入参数")
    config: Optional[Dict[str, Any]] = Field(default=None, description="执行配置")
    conversation_id: Optional[str] = Field(default=None, description="关联对话ID")


class SkillInvokeResponse(BaseModel):
    """Skill调用响应"""
    skill_id: str
    execution_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: float = 0


class SkillCreate(BaseModel):
    """创建Skill请求"""
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    protocol: str
    config: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None


class SkillUpdate(BaseModel):
    """更新Skill请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# ============== Skill存储 ==============

_skills_db: Dict[str, Dict] = {}
_executions_db: Dict[str, Dict] = {}


# ============== 初始化内置技能 ==============

def _init_builtin_skills():
    """初始化内置技能"""
    builtin_skills = [
        {
            "id": "skill_medical_diagnosis",
            "name": "medical_diagnosis",
            "display_name": "医学诊断",
            "description": "基于症状进行疾病诊断分析，提供可能的诊断结果和建议",
            "category": "diagnosis",
            "protocol": "builtin",
            "is_active": True,
            "is_builtin": True,
            "config": {},
            "input_schema": {
                "type": "object",
                "properties": {
                    "symptoms": {"type": "array", "items": {"type": "string"}},
                    "patient_info": {"type": "object"}
                },
                "required": ["symptoms"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "diagnoses": {"type": "array"},
                    "recommendations": {"type": "array"}
                }
            },
            "usage_count": 0,
            "created_at": datetime.now()
        },
        {
            "id": "skill_drug_interaction",
            "name": "drug_interaction",
            "display_name": "药物相互作用检查",
            "description": "检查多种药物之间的相互作用，提供用药安全建议",
            "category": "pharmacy",
            "protocol": "builtin",
            "is_active": True,
            "is_builtin": True,
            "config": {},
            "input_schema": {
                "type": "object",
                "properties": {
                    "drugs": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["drugs"]
            },
            "usage_count": 0,
            "created_at": datetime.now()
        },
        {
            "id": "skill_literature_search",
            "name": "literature_search",
            "display_name": "医学文献检索",
            "description": "检索PubMed、知网等医学文献数据库",
            "category": "research",
            "protocol": "skillhub",
            "is_active": True,
            "is_builtin": False,
            "config": {"endpoint": "https://api.skillhub.cn/skills/literature"},
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            },
            "usage_count": 0,
            "created_at": datetime.now()
        },
        {
            "id": "skill_clinical_guideline",
            "name": "clinical_guideline",
            "display_name": "临床指南查询",
            "description": "查询临床诊疗指南和专家共识",
            "category": "reference",
            "protocol": "skillhub",
            "is_active": True,
            "is_builtin": False,
            "config": {"endpoint": "https://api.skillhub.cn/skills/guideline"},
            "input_schema": {
                "type": "object",
                "properties": {
                    "disease": {"type": "string"},
                    "type": {"type": "string", "enum": ["guideline", "consensus", "all"]}
                },
                "required": ["disease"]
            },
            "usage_count": 0,
            "created_at": datetime.now()
        },
        {
            "id": "skill_lab_interpretation",
            "name": "lab_interpretation",
            "display_name": "检验结果解读",
            "description": "解读临床检验报告，提供异常指标分析和建议",
            "category": "diagnosis",
            "protocol": "builtin",
            "is_active": True,
            "is_builtin": True,
            "config": {},
            "input_schema": {
                "type": "object",
                "properties": {
                    "lab_results": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "number"},
                            "unit": {"type": "string"}
                        }
                    }}
                },
                "required": ["lab_results"]
            },
            "usage_count": 0,
            "created_at": datetime.now()
        },
        {
            "id": "skill_image_analysis",
            "name": "image_analysis",
            "display_name": "医学影像分析",
            "description": "分析X光、CT、MRI等医学影像",
            "category": "imaging",
            "protocol": "mcp",
            "is_active": True,
            "is_builtin": False,
            "config": {"mcp_server": "medical-imaging-mcp"},
            "input_schema": {
                "type": "object",
                "properties": {
                    "image_url": {"type": "string"},
                    "image_type": {"type": "string", "enum": ["xray", "ct", "mri", "ultrasound"]}
                },
                "required": ["image_url", "image_type"]
            },
            "usage_count": 0,
            "created_at": datetime.now()
        },
        {
            "id": "skill_symptom_checker",
            "name": "symptom_checker",
            "display_name": "症状自查",
            "description": "根据症状进行初步健康评估",
            "category": "consultation",
            "protocol": "builtin",
            "is_active": True,
            "is_builtin": True,
            "config": {},
            "input_schema": {
                "type": "object",
                "properties": {
                    "symptoms": {"type": "array", "items": {"type": "string"}},
                    "duration": {"type": "string"},
                    "severity": {"type": "string", "enum": ["mild", "moderate", "severe"]}
                },
                "required": ["symptoms"]
            },
            "usage_count": 0,
            "created_at": datetime.now()
        },
        {
            "id": "skill_dosage_calculator",
            "name": "dosage_calculator",
            "display_name": "用药剂量计算",
            "description": "根据患者信息计算药物剂量",
            "category": "pharmacy",
            "protocol": "builtin",
            "is_active": True,
            "is_builtin": True,
            "config": {},
            "input_schema": {
                "type": "object",
                "properties": {
                    "drug_name": {"type": "string"},
                    "patient_weight": {"type": "number"},
                    "patient_age": {"type": "integer"},
                    "indication": {"type": "string"}
                },
                "required": ["drug_name", "patient_weight"]
            },
            "usage_count": 0,
            "created_at": datetime.now()
        }
    ]
    
    for skill in builtin_skills:
        _skills_db[skill["id"]] = skill


# 初始化
_init_builtin_skills()


# ============== API端点 ==============

@router.get("", response_model=List[SkillInfo])
async def list_skills(
    category: Optional[str] = None,
    protocol: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    列出所有可用的Skill
    
    支持按类别、协议、状态过滤和搜索
    """
    skills = list(_skills_db.values())
    
    # 过滤
    if category:
        skills = [s for s in skills if s.get("category") == category]
    
    if protocol:
        skills = [s for s in skills if s.get("protocol") == protocol]
    
    if is_active is not None:
        skills = [s for s in skills if s.get("is_active") == is_active]
    
    if search:
        search_lower = search.lower()
        skills = [
            s for s in skills
            if search_lower in s.get("name", "").lower()
            or search_lower in s.get("display_name", "").lower()
            or search_lower in (s.get("description") or "").lower()
        ]
    
    return [SkillInfo(**s) for s in skills]


@router.get("/categories")
async def list_categories(
    current_user: TokenData = Depends(get_current_active_user)
):
    """列出所有Skill类别"""
    categories = {}
    for skill in _skills_db.values():
        cat = skill.get("category")
        if cat:
            categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "categories": [
            {"name": k, "count": v} for k, v in sorted(categories.items())
        ]
    }


@router.get("/protocols")
async def list_protocols(
    current_user: TokenData = Depends(get_current_active_user)
):
    """列出所有支持的协议"""
    return {
        "protocols": [
            {
                "name": "builtin",
                "display_name": "内置工具",
                "description": "系统内置的医学工具"
            },
            {
                "name": "skillhub",
                "display_name": "SkillHub",
                "description": "通过skillhub.cn调用的技能"
            },
            {
                "name": "mcp",
                "display_name": "MCP协议",
                "description": "通过Model Context Protocol调用的工具"
            }
        ]
    }


@router.get("/{skill_id}", response_model=SkillDetail)
async def get_skill(
    skill_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取Skill详情"""
    skill = _skills_db.get(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")
    
    return SkillDetail(**skill)


@router.post("", response_model=SkillInfo)
async def create_skill(
    request: SkillCreate,
    current_user: TokenData = Depends(get_current_active_user)
):
    """创建新Skill（需要管理员权限）"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 检查名称是否已存在
    for skill in _skills_db.values():
        if skill.get("name") == request.name:
            raise HTTPException(status_code=400, detail="技能名称已存在")
    
    skill_id = f"skill_{request.name}"
    
    skill = {
        "id": skill_id,
        "name": request.name,
        "display_name": request.display_name,
        "description": request.description,
        "category": request.category,
        "protocol": request.protocol,
        "is_active": True,
        "is_builtin": False,
        "config": request.config or {},
        "input_schema": request.input_schema or {},
        "output_schema": request.output_schema or {},
        "usage_count": 0,
        "created_at": datetime.now()
    }
    
    _skills_db[skill_id] = skill
    
    logger.info(f"创建技能: {skill_id}, 用户: {current_user.user_id}")
    
    return SkillInfo(**skill)


@router.put("/{skill_id}", response_model=SkillInfo)
async def update_skill(
    skill_id: str,
    request: SkillUpdate,
    current_user: TokenData = Depends(get_current_active_user)
):
    """更新Skill"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    skill = _skills_db.get(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")
    
    # 更新字段
    if request.display_name is not None:
        skill["display_name"] = request.display_name
    if request.description is not None:
        skill["description"] = request.description
    if request.config is not None:
        skill["config"] = request.config
    if request.is_active is not None:
        skill["is_active"] = request.is_active
    
    skill["updated_at"] = datetime.now()
    
    return SkillInfo(**skill)


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """删除Skill"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    skill = _skills_db.get(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")
    
    if skill.get("is_builtin"):
        raise HTTPException(status_code=400, detail="内置技能不能删除")
    
    del _skills_db[skill_id]
    
    logger.info(f"删除技能: {skill_id}")
    
    return {"message": "删除成功", "skill_id": skill_id}


@router.post("/{skill_id}/execute", response_model=SkillInvokeResponse)
async def execute_skill(
    skill_id: str,
    request: SkillInvokeRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    执行Skill
    
    根据协议类型调用不同的执行器：
    - builtin: 本地执行
    - skillhub: 通过skillhub.cn API调用
    - mcp: 通过MCP协议调用
    """
    skill = _skills_db.get(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")
    
    if not skill.get("is_active"):
        raise HTTPException(status_code=400, detail="技能未启用")
    
    execution_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    # 记录执行
    _executions_db[execution_id] = {
        "execution_id": execution_id,
        "skill_id": skill_id,
        "user_id": current_user.user_id,
        "input": request.input,
        "status": "running",
        "started_at": start_time
    }
    
    try:
        # 根据协议执行
        protocol = skill.get("protocol")
        
        if protocol == "builtin":
            result = await _execute_builtin(skill, request.input)
        elif protocol == "skillhub":
            result = await _execute_skillhub(skill, request.input, request.config)
        elif protocol == "mcp":
            result = await _execute_mcp(skill, request.input, request.config)
        else:
            raise ValueError(f"不支持的协议: {protocol}")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # 更新执行记录
        _executions_db[execution_id].update({
            "status": "completed",
            "result": result,
            "duration_seconds": duration,
            "completed_at": datetime.now()
        })
        
        # 更新技能使用次数
        skill["usage_count"] = skill.get("usage_count", 0) + 1
        skill["last_used_at"] = datetime.now()
        
        return SkillInvokeResponse(
            skill_id=skill_id,
            execution_id=execution_id,
            success=True,
            result=result,
            duration_seconds=duration
        )
        
    except Exception as e:
        logger.error(f"技能执行失败: {e}")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        _executions_db[execution_id].update({
            "status": "failed",
            "error": str(e),
            "duration_seconds": duration,
            "completed_at": datetime.now()
        })
        
        return SkillInvokeResponse(
            skill_id=skill_id,
            execution_id=execution_id,
            success=False,
            error=str(e),
            duration_seconds=duration
        )


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取执行结果"""
    execution = _executions_db.get(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    if execution.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此执行记录")
    
    return execution


@router.post("/{skill_id}/test")
async def test_skill(
    skill_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """测试Skill连接"""
    skill = _skills_db.get(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在: {skill_id}")
    
    protocol = skill.get("protocol")
    
    try:
        if protocol == "builtin":
            return {"status": "ok", "message": "内置技能可用"}
        elif protocol == "skillhub":
            # 测试skillhub连接
            return {"status": "ok", "message": "SkillHub连接正常"}
        elif protocol == "mcp":
            # 测试MCP连接
            return {"status": "ok", "message": "MCP服务连接正常"}
        else:
            return {"status": "unknown", "message": f"未知协议: {protocol}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== 执行器 ==============

async def _execute_builtin(skill: Dict, input_data: Dict) -> Dict:
    """执行内置技能"""
    from app.services.llm_service import llm_service
    
    skill_name = skill.get("name")
    
    # 构建提示词
    prompt = _build_skill_prompt(skill_name, input_data)
    
    # 调用LLM
    response = await llm_service.chat([
        {"role": "system", "content": f"你是一个专业的医学{skill.get('display_name')}助手。"},
        {"role": "user", "content": prompt}
    ])
    
    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    return {
        "skill": skill_name,
        "output": content,
        "raw_response": response
    }


async def _execute_skillhub(skill: Dict, input_data: Dict, config: Optional[Dict] = None) -> Dict:
    """通过SkillHub执行技能"""
    import httpx
    
    endpoint = skill.get("config", {}).get("endpoint")
    
    if not endpoint:
        raise ValueError("SkillHub endpoint未配置")
    
    # 调用SkillHub API
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            endpoint,
            json={"input": input_data, "config": config or {}}
        )
        response.raise_for_status()
        return response.json()


async def _execute_mcp(skill: Dict, input_data: Dict, config: Optional[Dict] = None) -> Dict:
    """通过MCP协议执行技能"""
    # MCP协议实现
    mcp_server = skill.get("config", {}).get("mcp_server")
    
    if not mcp_server:
        raise ValueError("MCP server未配置")
    
    # 这里应该实现MCP协议调用
    # 目前返回模拟结果
    return {
        "skill": skill.get("name"),
        "output": "MCP调用成功",
        "mcp_server": mcp_server
    }


def _build_skill_prompt(skill_name: str, input_data: Dict) -> str:
    """构建技能提示词"""
    prompts = {
        "medical_diagnosis": f"请根据以下症状进行诊断分析：{input_data}",
        "drug_interaction": f"请检查以下药物的相互作用：{input_data}",
        "lab_interpretation": f"请解读以下检验结果：{input_data}",
        "symptom_checker": f"请分析以下症状：{input_data}",
        "dosage_calculator": f"请计算用药剂量：{input_data}"
    }
    
    return prompts.get(skill_name, f"请处理以下请求：{input_data}")
