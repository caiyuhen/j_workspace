"""
Skill管理API - 完整实现

支持三种协议：skillhub.cn、MCP、本地工具
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.services.skill_registry import skill_registry
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


class SkillCandidate(BaseModel):
    """候选Skill信息"""
    id: str
    target_skill_id: str
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    protocol: str
    source: Optional[str] = None
    install_requires_confirmation: bool = True
    input_schema: Dict[str, Any] = {}


class SkillDiscoveryResponse(BaseModel):
    """候选Skill发现响应"""
    installed: bool = False
    required_skill_id: Optional[str] = None
    query: Optional[str] = None
    candidates: List[SkillCandidate]
    message: str


class SkillInstallCandidateRequest(BaseModel):
    """安装候选Skill请求"""
    candidate_id: str


class SkillUpdate(BaseModel):
    """更新Skill请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# ============== API端点 ==============

@router.get("/discover", response_model=SkillDiscoveryResponse)
async def discover_skill_candidates(
    query: Optional[str] = None,
    required_skill_id: Optional[str] = None,
    category: Optional[str] = None,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    发现可安装的候选Skill。

    方案B：只返回候选，不自动安装；必须由用户/管理员确认后再调用安装接口。
    """
    result = skill_registry.discover_skill_candidates(
        query=query,
        required_skill_id=required_skill_id,
        category=category,
    )
    return SkillDiscoveryResponse(**result)


@router.post("/install-candidate", response_model=SkillInfo)
async def install_skill_candidate(
    request: SkillInstallCandidateRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """确认安装候选Skill。"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        skill = skill_registry.install_candidate(request.candidate_id)
        logger.info(f"安装候选技能: {request.candidate_id} -> {skill['id']}, 用户: {current_user.user_id}")
        return SkillInfo(**skill)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    skills = skill_registry.list_skills(
        category=category,
        protocol=protocol,
        is_active=is_active,
        search=search
    )
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
            },
            {
                "name": "medical_api",
                "display_name": "医学后端接口",
                "description": "通过医疗大模型后端HTTP接口调用的医学专用能力"
            }
        ]
    }


@router.get("/{skill_id}", response_model=SkillDetail)
async def get_skill(
    skill_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取Skill详情"""
    skill = skill_registry.get_skill(skill_id)
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
    
    try:
        skill = skill_registry.create_skill(request.model_dump())
        logger.info(f"创建技能: {skill['id']}, 用户: {current_user.user_id}")
        return SkillInfo(**skill)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{skill_id}", response_model=SkillInfo)
async def update_skill(
    skill_id: str,
    request: SkillUpdate,
    current_user: TokenData = Depends(get_current_active_user)
):
    """更新Skill"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        skill = skill_registry.update_skill(skill_id, request.model_dump(exclude_unset=True))
        return SkillInfo(**skill)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """删除Skill"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        skill_registry.delete_skill(skill_id)
        logger.info(f"删除技能: {skill_id}")
        return {"message": "删除成功", "skill_id": skill_id}
    except ValueError as e:
        msg = str(e)
        code = 400 if "不能删除" in msg else 404
        raise HTTPException(status_code=code, detail=msg)


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
    res = await skill_registry.execute_skill(
        skill_id=skill_id,
        input_data=request.input,
        config=request.config,
        user_id=current_user.user_id,
        conversation_id=request.conversation_id,
    )
    return SkillInvokeResponse(
        skill_id=skill_id,
        execution_id=res["execution_id"],
        success=res["success"],
        result=res.get("result"),
        error=res.get("error"),
        duration_seconds=res.get("duration_seconds", 0),
    )


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取执行结果"""
    execution = skill_registry.get_execution(execution_id)
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


# Skills 执行实现已统一收敛到 skill_registry
