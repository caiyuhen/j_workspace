"""
代理管理API - 完整实现

提供代理查询、状态管理、任务调度等功能
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

from app.agents.registry import agent_registry
from app.agents.base import TaskContext, TaskResult, AgentStatus
from app.api.v1.auth import get_current_active_user, TokenData
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ============== 数据模型 ==============

class AgentInfo(BaseModel):
    """代理信息"""
    name: str  # 中文名称
    type: str  # 英文类型标识
    description: str
    capabilities: List[str]
    status: str
    last_active: Optional[datetime] = None
    task_count: int = 0
    success_rate: float = 1.0


class AgentDetail(BaseModel):
    """代理详情"""
    name: str
    type: str
    description: str
    capabilities: List[str]
    status: str
    config: Dict[str, Any] = {}
    statistics: Dict[str, Any] = {}
    last_active: Optional[datetime] = None


class TaskSubmit(BaseModel):
    """任务提交请求"""
    task_type: str = Field(..., description="任务类型")
    priority: str = Field(default="normal", description="优先级: low/normal/high/urgent")
    input: Dict[str, Any] = Field(..., description="任务输入")
    config: Dict[str, Any] = Field(default={}, description="任务配置")
    callback_url: Optional[str] = Field(default=None, description="回调URL")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    assigned_agents: List[str]
    created_at: datetime


class TaskResultResponse(BaseModel):
    """任务结果响应"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    completed_at: Optional[datetime] = None


class AgentStatusUpdate(BaseModel):
    """代理状态更新"""
    status: str
    reason: Optional[str] = None


# ============== 任务存储 ==============

_tasks_db: Dict[str, Dict] = {}


# ============== API端点 ==============

@router.get("", response_model=List[AgentInfo])
async def list_agents(
    status: Optional[str] = None,
    capability: Optional[str] = None,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    列出所有已注册的代理
    
    支持按状态和能力过滤，包含系统代理和自定义代理
    """
    agents = []
    
    # 添加系统代理
    for key, agent in agent_registry.agents.items():
        # 状态过滤
        if status and agent.status.value != status:
            continue
        
        # 能力过滤
        if capability and capability not in agent.capabilities:
            continue
        
        agents.append(AgentInfo(
            name=getattr(agent, 'display_name', agent.name),  # 使用中文名称
            type=getattr(agent, 'type', key),  # 使用英文类型
            description=agent.description,
            capabilities=agent.capabilities,
            status=agent.status.value,
            last_active=getattr(agent, '_last_active', None),
            task_count=getattr(agent, '_task_count', 0),
            success_rate=getattr(agent, '_success_rate', 1.0)
        ))
    
    # 添加自定义代理
    for agent_id, custom_agent in _custom_agents_db.items():
        # 状态过滤
        if status and custom_agent.get('status') != status:
            continue
        
        agents.append(AgentInfo(
            name=custom_agent['name'],
            type=custom_agent['type'],
            description=custom_agent.get('description', ''),
            capabilities=custom_agent.get('capabilities', []),
            status=custom_agent.get('status', 'idle'),
            last_active=None,
            task_count=0,
            success_rate=1.0
        ))
    
    return agents


@router.get("/status", response_model=Dict[str, str])
async def get_all_status(
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取所有代理状态"""
    return {
        name: agent.status.value 
        for name, agent in agent_registry.agents.items()
    }


@router.get("/capabilities")
async def list_capabilities(
    current_user: TokenData = Depends(get_current_active_user)
):
    """列出所有代理能力"""
    all_capabilities = set()
    
    for agent in agent_registry.agents.values():
        all_capabilities.update(agent.capabilities)
    
    return {
        "capabilities": sorted(list(all_capabilities)),
        "count": len(all_capabilities)
    }


@router.get("/{agent_name}", response_model=AgentDetail)
async def get_agent(
    agent_name: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取代理详情"""
    agent = agent_registry.get_agent(agent_name)
    
    # 如果找不到，尝试通过中文名称查找
    if not agent:
        for key, a in agent_registry.agents.items():
            if getattr(a, 'display_name', '') == agent_name or a.name == agent_name:
                agent = a
                agent_name = key
                break
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"代理不存在: {agent_name}")
    
    return AgentDetail(
        name=getattr(agent, 'display_name', agent.name),  # 中文名称
        type=getattr(agent, 'type', agent_name),  # 英文类型
        description=agent.description,
        capabilities=agent.capabilities,
        status=agent.status.value,
        config=getattr(agent, 'config', {}),
        statistics={
            "task_count": getattr(agent, '_task_count', 0),
            "success_count": getattr(agent, '_success_count', 0),
            "failure_count": getattr(agent, '_failure_count', 0),
            "success_rate": getattr(agent, '_success_rate', 1.0),
            "avg_duration": getattr(agent, '_avg_duration', 0)
        },
        last_active=getattr(agent, '_last_active', None)
    )


@router.post("/{agent_name}/execute")
async def execute_agent(
    agent_name: str,
    request: TaskSubmit,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    直接执行指定代理
    
    绕过编排代理，直接调用特定代理处理任务
    """
    agent = agent_registry.get_agent(agent_name)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"代理不存在: {agent_name}")
    
    if agent.status == AgentStatus.BUSY:
        raise HTTPException(status_code=503, detail="代理正忙，请稍后重试")
    
    task_id = str(uuid.uuid4())
    
    # 创建任务上下文
    context = TaskContext(
        task_id=task_id,
        user_id=current_user.user_id,
        conversation_id="",
        input=request.input,
        metadata={
            "task_type": request.task_type,
            "priority": request.priority,
            "config": request.config
        }
    )
    
    # 记录任务
    _tasks_db[task_id] = {
        "task_id": task_id,
        "agent_name": agent_name,
        "status": "running",
        "input": request.input,
        "created_at": datetime.now(),
        "user_id": current_user.user_id
    }
    
    try:
        # 执行代理
        start_time = datetime.now()
        result = await agent.execute(context)
        duration = (datetime.now() - start_time).total_seconds()
        
        # 更新任务记录
        _tasks_db[task_id].update({
            "status": "completed" if result.success else "failed",
            "result": result.output,
            "error": result.error,
            "duration_seconds": duration,
            "completed_at": datetime.now()
        })
        
        return {
            "task_id": task_id,
            "agent_name": agent_name,
            "success": result.success,
            "result": result.output,
            "error": result.error,
            "duration_seconds": duration
        }
        
    except Exception as e:
        logger.error(f"代理执行失败: {e}")
        _tasks_db[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now()
        })
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.post("/tasks", response_model=TaskResponse)
async def submit_task(
    request: TaskSubmit,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    提交任务到代理系统
    
    任务将通过编排代理自动分配给合适的专业代理处理
    """
    task_id = str(uuid.uuid4())
    
    # 记录任务
    _tasks_db[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "input": request.input,
        "task_type": request.task_type,
        "priority": request.priority,
        "created_at": datetime.now(),
        "user_id": current_user.user_id
    }
    
    # 创建任务上下文
    context = TaskContext(
        task_id=task_id,
        user_id=current_user.user_id,
        conversation_id="",
        input=request.input,
        metadata={
            "task_type": request.task_type,
            "priority": request.priority,
            "config": request.config,
            "callback_url": request.callback_url
        }
    )
    
    # 通过编排代理处理
    orchestrator = agent_registry.orchestrator
    
    if orchestrator:
        # 更新状态
        _tasks_db[task_id]["status"] = "running"
        
        try:
            result = await orchestrator.execute(context)
            
            # 安全获取agents_used
            assigned_agents = ["orchestrator"]
            if result.output and isinstance(result.output, dict):
                assigned_agents = result.output.get("agents_used", ["orchestrator"])
            
            _tasks_db[task_id].update({
                "status": "completed" if result.success else "failed",
                "result": result.output,
                "error": result.error,
                "assigned_agents": assigned_agents,
                "completed_at": datetime.now()
            })
            
        except Exception as e:
            _tasks_db[task_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now()
            })
    
    return TaskResponse(
        task_id=task_id,
        status=_tasks_db[task_id]["status"],
        assigned_agents=_tasks_db[task_id].get("assigned_agents", []),
        created_at=_tasks_db[task_id]["created_at"]
    )


@router.get("/tasks/{task_id}", response_model=TaskResultResponse)
async def get_task_result(
    task_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取任务结果"""
    task = _tasks_db.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    return TaskResultResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
        duration_seconds=task.get("duration_seconds"),
        completed_at=task.get("completed_at")
    )


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    current_user: TokenData = Depends(get_current_active_user)
):
    """列出用户的任务"""
    tasks = [
        task for task in _tasks_db.values()
        if task.get("user_id") == current_user.user_id
        and (status is None or task.get("status") == status)
    ]
    
    # 按时间排序
    tasks.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return {
        "tasks": tasks[:limit],
        "total": len(tasks)
    }


@router.post("/{agent_name}/reset")
async def reset_agent(
    agent_name: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """重置代理状态"""
    # 检查权限（仅管理员）
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    agent = agent_registry.get_agent(agent_name)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"代理不存在: {agent_name}")
    
    # 重置状态
    agent.status = AgentStatus.IDLE
    
    logger.info(f"代理 {agent_name} 已重置")
    
    return {"message": f"代理 {agent_name} 已重置", "status": "idle"}


@router.post("/dispatch")
async def dispatch_task(
    request: TaskSubmit,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    智能调度任务
    
    根据任务类型和代理状态，自动选择最合适的代理执行
    """
    task_id = str(uuid.uuid4())
    
    # 任务类型到代理的映射
    task_agent_mapping = {
        "diagnosis": "diagnosis",
        "clinical_diagnosis": "diagnosis",
        "research": "research",
        "literature_search": "research",
        "consultation": "consultation",
        "health_advice": "consultation",
        "knowledge_query": "knowledge",
        "guideline_search": "knowledge",
        "tool_call": "tool",
        "skill_invoke": "tool",
        "quality_check": "quality",
        "optimization": "learning"
    }
    
    # 确定目标代理
    task_type = request.task_type.lower()
    target_agent_name = task_agent_mapping.get(task_type, "orchestrator")
    
    agent = agent_registry.get_agent(target_agent_name)
    
    if not agent:
        target_agent_name = "orchestrator"
        agent = agent_registry.orchestrator
    
    # 检查代理状态
    if agent and agent.status == AgentStatus.BUSY:
        # 寻找替代代理
        for alt_name in ["orchestrator", "knowledge", "consultation"]:
            alt_agent = agent_registry.get_agent(alt_name)
            if alt_agent and alt_agent.status == AgentStatus.IDLE:
                target_agent_name = alt_name
                agent = alt_agent
                break
    
    # 创建任务上下文
    context = TaskContext(
        task_id=task_id,
        user_id=current_user.user_id,
        conversation_id="",
        input=request.input,
        metadata={
            "task_type": request.task_type,
            "priority": request.priority,
            "config": request.config
        }
    )
    
    # 记录任务
    _tasks_db[task_id] = {
        "task_id": task_id,
        "agent_name": target_agent_name,
        "status": "running",
        "input": request.input,
        "created_at": datetime.now(),
        "user_id": current_user.user_id
    }
    
    try:
        # 执行
        start_time = datetime.now()
        result = await agent.execute(context) if agent else None
        duration = (datetime.now() - start_time).total_seconds()
        
        if result:
            _tasks_db[task_id].update({
                "status": "completed" if result.success else "failed",
                "result": result.output,
                "error": result.error,
                "duration_seconds": duration,
                "completed_at": datetime.now()
            })
        
        return {
            "task_id": task_id,
            "dispatched_to": target_agent_name,
            "success": result.success if result else False,
            "result": result.output if result else None,
            "error": result.error if result else "No agent available",
            "duration_seconds": duration
        }
        
    except Exception as e:
        logger.error(f"任务调度失败: {e}")
        _tasks_db[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now()
        })
        raise HTTPException(status_code=500, detail=f"调度失败: {str(e)}")


# ============== 代理注册 API ==============

class AgentRegister(BaseModel):
    """代理注册请求"""
    name: str
    type: str
    description: str = ""
    config: Dict[str, Any] = {}
    capabilities: List[str] = []


# 已注册的自定义代理存储
_custom_agents_db: Dict[str, Dict[str, Any]] = {}


@router.post("/register")
async def register_agent(
    agent: AgentRegister,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    注册新代理
    
    允许用户注册自定义代理或从在线仓库安装代理
    """
    # 检查权限（仅管理员可以注册）
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    agent_id = str(uuid.uuid4())
    
    # 创建代理记录
    agent_record = {
        "id": agent_id,
        "name": agent.name,
        "type": agent.type,
        "description": agent.description,
        "config": agent.config,
        "capabilities": agent.capabilities,
        "status": "idle",
        "created_at": datetime.now(),
        "created_by": current_user.user_id,
        "is_custom": True
    }
    
    _custom_agents_db[agent_id] = agent_record
    
    logger.info(f"新代理已注册: {agent.name} (ID: {agent_id})")
    
    return {
        "message": f"代理 '{agent.name}' 注册成功",
        "agent_id": agent_id,
        "agent": agent_record
    }


@router.get("/custom")
async def list_custom_agents(
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取已注册的自定义代理列表"""
    return {
        "total": len(_custom_agents_db),
        "agents": list(_custom_agents_db.values())
    }


@router.delete("/custom/{agent_id}")
async def delete_custom_agent(
    agent_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """删除自定义代理"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    if agent_id not in _custom_agents_db:
        raise HTTPException(status_code=404, detail="代理不存在")
    
    agent_name = _custom_agents_db[agent_id]["name"]
    del _custom_agents_db[agent_id]
    
    return {"message": f"代理 '{agent_name}' 已删除"}


# ============== 自学习闭环 API ==============

class FeedbackSubmit(BaseModel):
    """反馈提交请求"""
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    feedback_type: str = Field(..., description="反馈类型: positive/negative/suggestion")
    content: str = Field(..., description="反馈内容")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分1-5")
    tags: List[str] = Field(default=[], description="标签")


class LearningRecord(BaseModel):
    """学习记录"""
    id: str
    type: str
    content: Dict[str, Any]
    created_at: datetime
    processed: bool = False


# 模拟学习数据存储
_learning_db: Dict[str, LearningRecord] = {}
_feedback_db: List[Dict[str, Any]] = []


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackSubmit,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    提交用户反馈
    
    用户可以对代理的回复进行评价，系统将自动学习改进
    """
    feedback_id = str(uuid.uuid4())
    
    # 保存反馈
    feedback_record = {
        "id": feedback_id,
        "user_id": current_user.user_id,
        "conversation_id": feedback.conversation_id,
        "message_id": feedback.message_id,
        "feedback_type": feedback.feedback_type,
        "content": feedback.content,
        "rating": feedback.rating,
        "tags": feedback.tags,
        "created_at": datetime.now(),
        "processed": False
    }
    _feedback_db.append(feedback_record)
    
    # 触发学习代理进行反馈学习
    learning_agent = agent_registry.get_agent("learning")
    if learning_agent:
        # 异步触发学习任务
        try:
            context = TaskContext(
                task_id=str(uuid.uuid4()),
                input={
                    "type": feedback.feedback_type,
                    "content": feedback.content,
                    "rating": feedback.rating,
                    "conversation_id": feedback.conversation_id
                },
                metadata={"task_type": "feedback_learning"}
            )
            # 不等待结果，异步执行
            result = await learning_agent.execute(context)
            if result.success:
                feedback_record["processed"] = True
                feedback_record["learning_result"] = result.output
        except Exception as e:
            logger.error(f"反馈学习失败: {e}")
    
    return {
        "message": "反馈已提交，系统将自动学习改进",
        "feedback_id": feedback_id,
        "processed": feedback_record.get("processed", False)
    }


@router.get("/feedback/list")
async def list_feedback(
    limit: int = 20,
    offset: int = 0,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取反馈列表"""
    # 管理员可以查看所有反馈，普通用户只能查看自己的
    if current_user.role == "admin":
        feedbacks = _feedback_db
    else:
        feedbacks = [f for f in _feedback_db if f["user_id"] == current_user.user_id]
    
    total = len(feedbacks)
    items = feedbacks[offset:offset + limit]
    
    return {
        "total": total,
        "items": items
    }


@router.post("/learning/trigger")
async def trigger_learning(
    task_type: str = "effect_evaluation",
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    触发学习任务
    
    支持的学习任务类型：
    - feedback_learning: 反馈学习
    - knowledge_update: 知识更新
    - effect_evaluation: 效果评估
    - trend_analysis: 趋势分析
    """
    learning_agent = agent_registry.get_agent("learning")
    if not learning_agent:
        raise HTTPException(status_code=404, detail="学习代理不可用")
    
    task_id = str(uuid.uuid4())
    
    # 收集学习数据
    learning_input = {}
    if task_type == "effect_evaluation":
        # 收集效果评估数据
        total_tasks = len(_tasks_db)
        successful_tasks = len([t for t in _tasks_db.values() if t.get("status") == "completed"])
        learning_input = {
            "period": "daily",
            "metrics": {
                "total_tasks": total_tasks,
                "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
                "feedback_count": len(_feedback_db),
                "positive_feedback": len([f for f in _feedback_db if f["feedback_type"] == "positive"])
            }
        }
    elif task_type == "trend_analysis":
        learning_input = {
            "data_type": "usage",
            "time_range": "7d"
        }
    
    context = TaskContext(
        task_id=task_id,
        input=learning_input,
        metadata={"task_type": task_type}
    )
    
    result = await learning_agent.execute(context)
    
    # 保存学习记录
    learning_record = LearningRecord(
        id=task_id,
        type=task_type,
        content=result.output if result.success else {"error": result.error},
        created_at=datetime.now(),
        processed=result.success
    )
    _learning_db[task_id] = learning_record
    
    return {
        "task_id": task_id,
        "task_type": task_type,
        "success": result.success,
        "result": result.output,
        "error": result.error
    }


@router.get("/learning/records")
async def list_learning_records(
    limit: int = 20,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取学习记录"""
    records = list(_learning_db.values())
    records.sort(key=lambda x: x.created_at, reverse=True)
    
    return {
        "total": len(records),
        "items": [
            {
                "id": r.id,
                "type": r.type,
                "content": r.content,
                "created_at": r.created_at,
                "processed": r.processed
            }
            for r in records[:limit]
        ]
    }


@router.get("/learning/stats")
async def get_learning_stats(
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取学习统计"""
    total_feedback = len(_feedback_db)
    positive_feedback = len([f for f in _feedback_db if f["feedback_type"] == "positive"])
    negative_feedback = len([f for f in _feedback_db if f["feedback_type"] == "negative"])
    processed_feedback = len([f for f in _feedback_db if f.get("processed")])
    
    total_tasks = len(_tasks_db)
    successful_tasks = len([t for t in _tasks_db.values() if t.get("status") == "completed"])
    
    return {
        "feedback": {
            "total": total_feedback,
            "positive": positive_feedback,
            "negative": negative_feedback,
            "processed": processed_feedback,
            "satisfaction_rate": positive_feedback / total_feedback if total_feedback > 0 else 0
        },
        "tasks": {
            "total": total_tasks,
            "successful": successful_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0
        },
        "learning_records": len(_learning_db)
    }
