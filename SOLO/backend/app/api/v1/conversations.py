"""
对话管理API - 完整实现

提供对话创建、消息发送、历史查询等功能
大模型服务通过 `/chat` 接口提供内置RAG能力
"""
from fastapi import APIRouter, HTTPException, Depends, Query
import threading
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import json
import logging

from app.agents.registry import agent_registry
from app.agents.base import TaskContext
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import llm_service
from app.api.v1.auth import get_current_active_user, TokenData
from app.core.auth import fake_users_db, get_password_hash
from app.core.database import AsyncSessionLocal, get_db
from app.models import Conversation, ConversationStatus, Message, SubTask, Task, TaskStatus, User, UserRole
from app.services.task_background_service import build_task_started_result, launch_task_in_background
from app.services.task_execution_service import task_runner
from app.services.task_progress_service import build_task_progress

logger = logging.getLogger(__name__)
router = APIRouter()


_MESSAGE_ROLE_ORDER = {"user": 0, "assistant": 1, "system": 2}


def _message_display_sort_key(message: Message):
    """消息展示排序：同一时间戳时，用户提示词必须排在助手状态消息之前。"""
    return (
        message.created_at or datetime.min,
        _MESSAGE_ROLE_ORDER.get(message.role, 9),
        message.id,
    )


# ============== 数据模型 ==============

class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """对话响应"""
    id: str
    title: Optional[str]
    status: str = "active"
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    items: List[ConversationResponse]
    total: int
    page: int
    page_size: int


class MessageCreate(BaseModel):
    """创建消息请求"""
    content: str = Field(..., description="消息内容", min_length=1)
    input_type: str = Field(default="text", description="输入类型: text/voice")
    model: Optional[str] = Field(default=None, description="指定LLM模型")
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    conversation_id: str
    role: str
    content: str
    tokens: Optional[int] = None
    references: Optional[List[Dict]] = None
    created_at: datetime


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    execution_mode: str = "chat"
    deliverable_format: str = "md"
    stream: bool = False


class ArtifactResponse(BaseModel):
    """交付物响应"""
    artifact_id: str
    task_id: str
    filename: str
    format: str
    download_url: str
    created_at: datetime


class SubTaskResponse(BaseModel):
    """子任务响应"""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    error_message: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    conversation_id: str
    message: MessageResponse
    agent_used: str
    task_id: Optional[str] = None
    task_status: Optional[str] = None
    async_execution: bool = False
    waiting_for_skill: bool = False
    skill_resolution: Optional[Dict[str, Any]] = None
    subtasks: List[SubTaskResponse] = []
    artifacts: List[ArtifactResponse] = []


class TaskProgressResponse(BaseModel):
    """任务进度响应"""
    task_id: str
    conversation_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: str
    status: str
    progress_percent: int
    summary: Dict[str, int]
    subtasks: List[Dict[str, Any]]
    artifacts: List[Dict[str, Any]] = []
    result: Dict[str, Any] = {}
    waiting_for_skill: bool = False
    skill_resolution: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None
    started_at: Optional[Any] = None
    completed_at: Optional[Any] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None


class LLMModelResponse(BaseModel):
    """LLM模型配置响应（不包含密钥）"""
    name: str
    display_name: str
    type: str = "openai"
    default: bool = False


# ============== 引用内容处理 ==============

REFERENCE_SOURCE_ALIASES = {
    "milvus": "Milvus",
    "pubmed": "PubMed",
    "pmid": "PubMed",
    "ensembl": "Ensembl",
    "chembl": "ChEMBL",
    "fda": "FDA",
    "clinicaltrials": "ClinicalTrials",
    "clinicaltrials.gov": "ClinicalTrials",
    "clinical_trials": "ClinicalTrials",
    "clinical-trials": "ClinicalTrials",
}


# ============== API端点 ==============

@router.get("/llm-models", response_model=List[LLMModelResponse])
async def list_llm_models(
    current_user: TokenData = Depends(get_current_active_user),
):
    """获取可在聊天页面选择的LLM模型列表。"""
    return llm_service.get_model_configs()


@router.get("/tasks/{task_id}/progress", response_model=TaskProgressResponse)
async def get_task_progress(
    task_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 Chat 任务执行进度、子任务详情和交付物列表。"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此任务")

    subtask_result = await db.execute(
        select(SubTask).where(SubTask.task_id == task_id).order_by(SubTask.created_at.asc())
    )
    subtasks = list(subtask_result.scalars().all())
    return TaskProgressResponse(**build_task_progress(task, subtasks))


@router.post("/tasks/{task_id}/resume", response_model=TaskProgressResponse)
async def resume_waiting_task(
    task_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """安装缺失 Skill 后继续执行等待中的 Chat 任务。"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此任务")
    if task.status != TaskStatus.WAITING_FOR_SKILL:
        raise HTTPException(status_code=400, detail="任务当前不在等待 Skill 状态")

    config = task.config or {}
    await task_runner.execute(
        db=db,
        task=task,
        user_id=current_user.user_id,
        conversation_id=task.conversation_id or "",
        prompt=task.description or task.title or "继续执行任务",
        model=config.get("model"),
        deliverable_format=config.get("deliverable_format") or "md",
    )

    subtask_result = await db.execute(
        select(SubTask).where(SubTask.task_id == task_id).order_by(SubTask.created_at.asc())
    )
    subtasks = list(subtask_result.scalars().all())
    return TaskProgressResponse(**build_task_progress(task, subtasks))


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话列表
    
    支持分页和状态过滤
    """
    await _ensure_current_user_exists(db, current_user)

    conditions = [Conversation.user_id == current_user.user_id]
    if status:
        conditions.append(Conversation.status == _conversation_status(status))

    total_result = await db.execute(
        select(func.count()).select_from(Conversation).where(*conditions)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(Conversation)
        .where(*conditions)
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    
    return ConversationListResponse(
        items=[_conversation_to_response(item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新对话"""
    await _ensure_current_user_exists(db, current_user)
    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        title=request.title or "新对话",
        status=ConversationStatus.ACTIVE,
        message_count=0,
        context=request.context or {},
        total_tokens=0,
    )
    db.add(conversation)
    await db.flush()
    
    logger.info(f"创建对话: {conversation.id}, 用户: {current_user.user_id}")
    
    return _conversation_to_response(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取对话详情"""
    conversation = await _get_owned_conversation(db, conversation_id, current_user.user_id)
    return _conversation_to_response(conversation)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除对话"""
    conversation = await _get_owned_conversation(db, conversation_id, current_user.user_id)
    conversation.status = ConversationStatus.DELETED
    conversation.updated_at = datetime.now()
    await db.flush()
    
    logger.info(f"删除对话: {conversation_id}")
    
    return {"message": "删除成功", "conversation_id": conversation_id}


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    before: Optional[str] = None,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取对话消息列表"""
    await _get_owned_conversation(db, conversation_id, current_user.user_id)

    query = select(Message).where(Message.conversation_id == conversation_id)
    if before:
        before_message = await db.get(Message, before)
        if before_message and before_message.conversation_id == conversation_id:
            query = query.where(Message.created_at < before_message.created_at)

    result = await db.execute(
        query.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)
    )
    messages = sorted(result.scalars().all(), key=_message_display_sort_key)
    
    return [_message_to_response(msg) for msg in messages]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息并获取响应。

    页面选择哪个LLM模型，就只调用该LLM模型；不再自动进入编排代理或技能链路。
    """
    await _ensure_current_user_exists(db, current_user)
    conversation = await _get_or_create_conversation(
        db,
        current_user.user_id,
        request.message,
        request.conversation_id,
    )
    conversation_id = conversation.id
    
    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        tokens=0,
        references=[],
    )
    db.add(user_message)
    await db.flush()
    
    try:
        # 构建消息历史
        history_messages = await _get_recent_messages(db, conversation_id, limit=20)
        chat_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
        ]
        
        execution_mode = (request.execution_mode or "chat").lower()
        artifacts: List[Dict[str, Any]] = []
        subtasks: List[Dict[str, Any]] = []
        async_execution = False
        waiting_for_skill = False
        skill_resolution: Optional[Dict[str, Any]] = None
        task_id: Optional[str] = None
        task_status: Optional[str] = None

        if execution_mode == "task":
            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                user_id=current_user.user_id,
                conversation_id=conversation_id,
                title=request.message[:80],
                description=request.message,
                task_type="chat_task",
                status=TaskStatus.RUNNING,
                config={
                    "model": request.model,
                    "deliverable_format": request.deliverable_format,
                    "source": "chat",
                },
                assigned_agents=["llm"],
                started_at=datetime.now(),
            )
            db.add(task)
            await db.flush()
            # 后台线程使用独立数据库连接；必须先提交，否则线程查询不到刚创建的任务。
            await db.commit()

            deliverable_format = (request.deliverable_format or "md").lower()
            logger.info("=== 开始启动后台线程: task_id=%s, user=%s ===", task_id, current_user.user_id)
            launch_task_in_background(
                task_id=task_id,
                user_id=current_user.user_id,
                conversation_id=conversation_id,
                prompt=request.message,
                model=request.model,
                deliverable_format=deliverable_format,
            )
            logger.info("=== 后台线程已启动: task_id=%s ===", task_id)

            result = build_task_started_result(task_id)
            response_content = result["content"]
            response_references = []
            async_execution = True
            task_status = result["task_status"]
            agent_used = "task"
        else:
            # 页面选择哪个LLM模型，就只调用该LLM模型；不再经过编排代理或技能链路。
            logger.info("直接调用所选LLM模型: model=%s", request.model)
            response = await llm_service.chat(
                chat_messages,
                session_id=conversation_id,
                model=request.model
            )
            response_content = _extract_content(response)
            response_references = _extract_references(response)
            agent_used = "llm"
        
        # 计算token
        tokens = llm_service.count_messages_tokens(chat_messages)
        
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=response_content,
            tokens=tokens,
            references=response_references,
        )
        db.add(assistant_message)
        await db.flush()
        await _refresh_conversation_stats(db, conversation)
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=_message_to_response(assistant_message),
            agent_used=agent_used,
            task_id=task_id,
            task_status=task_status,
            async_execution=async_execution,
            waiting_for_skill=waiting_for_skill,
            skill_resolution=skill_resolution,
            subtasks=[SubTaskResponse(**subtask) for subtask in subtasks],
            artifacts=[ArtifactResponse(**artifact) for artifact in artifacts],
        )
        
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    流式聊天接口
    
    返回SSE格式的流式响应
    """
    await _ensure_current_user_exists(db, current_user)
    conversation = await _get_or_create_conversation(
        db,
        current_user.user_id,
        request.message,
        request.conversation_id,
    )
    conversation_id = conversation.id

    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="user",
        content=request.message,
        tokens=0,
        references=[],
    )
    db.add(user_message)
    await db.flush()
    history_messages = await _get_recent_messages(db, conversation_id, limit=20)
    chat_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in history_messages
    ]
    await db.commit()
    
    async def generate():
        """生成流式响应"""
        try:
            full_content = ""
            
            # 流式调用LLM
            async for chunk in llm_service.stream_chat(
                chat_messages,
                session_id=conversation_id,
                model=request.model
            ):
                full_content += chunk
                yield f"data: {json.dumps({'content': chunk, 'conversation_id': conversation_id})}\n\n"
            
            async with AsyncSessionLocal() as stream_db:
                stream_conversation = await stream_db.get(Conversation, conversation_id)
                assistant_message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_content,
                    tokens=llm_service.count_messages_tokens(chat_messages),
                    references=[],
                )
                stream_db.add(assistant_message)
                await stream_db.flush()
                if stream_conversation:
                    await _refresh_conversation_stats(stream_db, stream_conversation)
                await stream_db.commit()
            
            yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
            
        except Exception as e:
            logger.error(f"流式处理失败: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: MessageCreate,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    发送消息到指定对话
    
    消息将通过编排代理处理，自动进行意图识别、任务分解、代理调度
    """
    conversation = await _get_owned_conversation(db, conversation_id, current_user.user_id)
    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="user",
        content=request.content,
        tokens=0,
        references=[],
        meta=request.metadata or {},
    )
    db.add(user_message)
    await db.flush()
    
    try:
        # 构建消息历史
        history_messages = await _get_recent_messages(db, conversation_id, limit=20)
        chat_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
        ]
        
        # 调用LLM
        response = await llm_service.chat(
            chat_messages,
            session_id=conversation_id,
            model=request.model
        )
        response_content = _extract_content(response)
        response_references = _extract_references(response)
        
        # 计算token
        tokens = llm_service.count_messages_tokens(chat_messages)
        
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=response_content,
            tokens=tokens,
            references=response_references,
        )
        db.add(assistant_message)
        await db.flush()
        await _refresh_conversation_stats(db, conversation)
        
        return _message_to_response(assistant_message)
        
    except Exception as e:
        logger.error(f"消息处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """归档对话"""
    conversation = await _get_owned_conversation(db, conversation_id, current_user.user_id)
    conversation.status = ConversationStatus.ARCHIVED
    conversation.updated_at = datetime.now()
    await db.flush()
    
    return {"message": "归档成功", "conversation_id": conversation_id}


@router.post("/{conversation_id}/optimize")
async def optimize_prompt(
    conversation_id: str,
    message_id: str,
    current_user: TokenData = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    一键优化提示词
    
    使用学习代理优化用户输入的提示词
    """
    await _get_owned_conversation(db, conversation_id, current_user.user_id)
    target_message = await db.get(Message, message_id)
    
    if not target_message or target_message.conversation_id != conversation_id or target_message.role != "user":
        raise HTTPException(status_code=404, detail="消息不存在或不是用户消息")
    
    # 使用学习代理优化提示词
    learning_agent = agent_registry.get_agent("learning")
    if learning_agent:
        context = TaskContext(
            task_id=str(uuid.uuid4()),
            user_id=current_user.user_id,
            conversation_id=conversation_id,
            input=target_message.content,
            metadata={"task_type": "optimize_prompt"}
        )
        result = await learning_agent.execute(context)
        optimized_prompt = result.output.get("optimized_prompt", target_message.content) if result.output else target_message.content
    else:
        # 简单优化：添加医学上下文
        optimized_prompt = f"作为医学专家，请详细分析：{target_message.content}"
    
    return {
        "original_prompt": target_message.content,
        "optimized_prompt": optimized_prompt,
        "message_id": message_id
    }


# ============== 辅助函数 ==============

def _enum_value(value: Any) -> Any:
    """返回枚举或普通值的可序列化值。"""
    return getattr(value, "value", value)


def _conversation_status(status: str) -> ConversationStatus:
    """将请求中的状态字符串转换为对话状态枚举。"""
    try:
        return ConversationStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的对话状态: {status}")




def _conversation_to_response(conversation: Conversation) -> ConversationResponse:
    """将数据库对话模型转换为接口响应。"""
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        status=_enum_value(conversation.status),
        message_count=conversation.message_count or 0,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _message_to_response(message: Message) -> MessageResponse:
    """将数据库消息模型转换为接口响应。"""
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        tokens=message.tokens or 0,
        references=message.references or [],
        created_at=message.created_at,
    )


async def _ensure_current_user_exists(db: AsyncSession, current_user: TokenData) -> None:
    """确保认证系统中的内存用户在数据库中存在，满足对话外键约束。"""
    if not current_user.user_id:
        raise HTTPException(status_code=401, detail="无效的用户信息")

    existing_user = await db.get(User, current_user.user_id)
    if existing_user:
        return

    fake_user = fake_users_db.get(current_user.email or "", {})
    role = fake_user.get("role") or current_user.role or UserRole.USER.value
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.USER

    email = current_user.email or f"{current_user.user_id}@local"
    email_result = await db.execute(select(User).where(User.email == email))
    if email_result.scalar_one_or_none():
        email = f"{current_user.user_id}-{email}"

    user = User(
        id=current_user.user_id,
        email=email,
        hashed_password=fake_user.get("hashed_password") or get_password_hash(str(uuid.uuid4())),
        name=fake_user.get("name") or current_user.email or current_user.user_id,
        role=user_role,
        is_active=True,
    )
    db.add(user)
    await db.flush()


async def _get_owned_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
) -> Conversation:
    """获取当前用户拥有的对话。"""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conversation.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    return conversation


async def _get_or_create_conversation(
    db: AsyncSession,
    user_id: str,
    first_message: str,
    conversation_id: Optional[str] = None,
) -> Conversation:
    """获取已有对话，或在新会话/旧 ID 丢失时创建对话。"""
    if conversation_id:
        conversation = await db.get(Conversation, conversation_id)
        if conversation:
            if conversation.user_id != user_id:
                raise HTTPException(status_code=403, detail="无权访问此对话")
            return conversation

    conversation = Conversation(
        id=conversation_id or str(uuid.uuid4()),
        user_id=user_id,
        title=first_message[:50] + ("..." if len(first_message) > 50 else ""),
        status=ConversationStatus.ACTIVE,
        message_count=0,
        context={},
        total_tokens=0,
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def _get_recent_messages(
    db: AsyncSession,
    conversation_id: str,
    limit: int = 20,
) -> List[Message]:
    """读取最近若干条消息，并按时间正序返回。"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def _refresh_conversation_stats(db: AsyncSession, conversation: Conversation) -> None:
    """刷新对话消息数、token 数和更新时间。"""
    count_result = await db.execute(
        select(func.count()).select_from(Message).where(Message.conversation_id == conversation.id)
    )
    tokens_result = await db.execute(
        select(func.coalesce(func.sum(Message.tokens), 0)).where(Message.conversation_id == conversation.id)
    )
    conversation.message_count = count_result.scalar_one()
    conversation.total_tokens = tokens_result.scalar_one()
    conversation.updated_at = datetime.now()
    await db.flush()


def _extract_content(response: Dict) -> str:
    """从LLM响应中提取内容"""
    if "choices" in response:
        return response["choices"][0].get("message", {}).get("content", "")
    elif "content" in response:
        return response["content"]
    else:
        return str(response)


def _normalize_reference_source(raw_source: Any) -> str:
    """规范化引用来源名称。"""
    source = str(raw_source or "").strip()
    if not source:
        return "Unknown"
    key = source.lower().replace(" ", "")
    return REFERENCE_SOURCE_ALIASES.get(key, source)


def _first_present(data: Dict, keys: List[str], default: Any = None) -> Any:
    """按顺序返回字典中第一个存在且非空的值。"""
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def _infer_reference_source(item: Dict) -> str:
    """从引用条目的字段推断来源类型。"""
    explicit_source = _first_present(
        item,
        ["source_type", "source", "database", "db", "provider", "origin", "collection"],
    )
    if explicit_source:
        return _normalize_reference_source(explicit_source)

    if _first_present(item, ["pmid", "pubmed_id"]):
        return "PubMed"
    if _first_present(item, ["nct_id", "nctId", "clinical_trial_id"]):
        return "ClinicalTrials"
    if _first_present(item, ["chembl_id", "molecule_chembl_id", "assay_chembl_id"]):
        return "ChEMBL"
    if _first_present(item, ["ensembl_id", "gene_id", "transcript_id"]):
        return "Ensembl"
    if _first_present(item, ["fda_application_number", "application_number", "label_url"]):
        return "FDA"
    if _first_present(item, ["score", "distance", "similarity"]):
        return "Milvus"
    return "Unknown"


def _normalize_reference_item(item: Any, index: int) -> Optional[Dict[str, Any]]:
    """将不同接口返回的引用条目统一为前端可展示结构。"""
    if item is None:
        return None

    if not isinstance(item, dict):
        return {
            "id": f"ref-{index}",
            "source_type": "Unknown",
            "title": f"引用 {index + 1}",
            "content": str(item),
            "metadata": {},
        }

    source_type = _infer_reference_source(item)
    title = _first_present(
        item,
        ["title", "name", "article_title", "study_title", "brief_title", "drug_name", "gene_symbol", "symbol"],
        f"{source_type} 引用 {index + 1}",
    )
    content = _first_present(
        item,
        ["content", "text", "abstract", "summary", "snippet", "chunk", "description", "label", "result"],
        "",
    )
    url = _first_present(item, ["url", "link", "href", "source_url"])
    identifier = _first_present(
        item,
        ["pmid", "pubmed_id", "nct_id", "nctId", "chembl_id", "ensembl_id", "gene_id", "id", "document_id"],
    )
    score = _first_present(item, ["score", "similarity", "distance", "rank_score"])

    normalized = {
        "id": str(identifier or f"ref-{index}"),
        "source_type": source_type,
        "title": str(title),
        "content": str(content) if content is not None else "",
        "url": url,
        "score": score,
        "metadata": item,
    }

    # 去掉空值，减少前端判断复杂度。
    return {k: v for k, v in normalized.items() if v not in (None, "", [], {})}


def _extract_references(response: Any) -> List[Dict[str, Any]]:
    """从 LLM / agent 响应中提取并标准化引用内容。"""
    if not isinstance(response, dict):
        return []

    raw_references = _first_present(
        response,
        ["references", "sources", "retrieved_knowledge", "citations"],
        [],
    )

    raw_response = response.get("raw_response")
    if not raw_references and isinstance(raw_response, dict):
        raw_references = _first_present(
            raw_response,
            ["references", "sources", "retrieved_knowledge", "citations"],
            [],
        )

    if isinstance(raw_references, dict):
        raw_references = [raw_references]
    if not isinstance(raw_references, list):
        return []

    normalized = []
    for index, item in enumerate(raw_references):
        ref = _normalize_reference_item(item, index)
        if ref:
            normalized.append(ref)
    return normalized
