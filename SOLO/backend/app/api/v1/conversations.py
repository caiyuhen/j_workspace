"""
对话管理API - 完整实现

提供对话创建、消息发送、历史查询等功能
大模型服务(192.168.0.214:8802/chat/)已内置RAG能力
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import json
import logging

from app.agents.registry import agent_registry
from app.agents.base import TaskContext
from app.services.llm_service import llm_service
from app.api.v1.auth import get_current_active_user, TokenData

logger = logging.getLogger(__name__)
router = APIRouter()


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
    agent_type: Optional[str] = Field(default=None, description="指定代理类型")
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    conversation_id: str
    role: str
    content: str
    agent_type: Optional[str] = None
    tokens: Optional[int] = None
    references: Optional[List[Dict]] = None
    created_at: datetime


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    agent_type: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """聊天响应"""
    conversation_id: str
    message: MessageResponse
    agent_used: str


# ============== 模拟数据存储（实际应使用数据库） ==============

# 对话存储
_conversations_db: Dict[str, Dict] = {}
# 消息存储
_messages_db: Dict[str, List[Dict]] = {}


# ============== API端点 ==============

@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    获取对话列表
    
    支持分页和状态过滤
    """
    # 过滤用户的对话
    user_conversations = [
        conv for conv in _conversations_db.values()
        if conv.get("user_id") == current_user.user_id
        and (status is None or conv.get("status") == status)
    ]
    
    # 按更新时间排序
    user_conversations.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=True)
    
    # 分页
    total = len(user_conversations)
    start = (page - 1) * page_size
    end = start + page_size
    items = user_conversations[start:end]
    
    return ConversationListResponse(
        items=[ConversationResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    current_user: TokenData = Depends(get_current_active_user)
):
    """创建新对话"""
    conversation_id = str(uuid.uuid4())
    now = datetime.now()
    
    conversation = {
        "id": conversation_id,
        "user_id": current_user.user_id,
        "title": request.title or "新对话",
        "status": "active",
        "message_count": 0,
        "context": request.context or {},
        "created_at": now,
        "updated_at": now
    }
    
    _conversations_db[conversation_id] = conversation
    _messages_db[conversation_id] = []
    
    logger.info(f"创建对话: {conversation_id}, 用户: {current_user.user_id}")
    
    return ConversationResponse(**conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取对话详情"""
    conversation = _conversations_db.get(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    return ConversationResponse(**conversation)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """删除对话"""
    conversation = _conversations_db.get(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权删除此对话")
    
    # 软删除
    conversation["status"] = "deleted"
    conversation["updated_at"] = datetime.now()
    
    logger.info(f"删除对话: {conversation_id}")
    
    return {"message": "删除成功", "conversation_id": conversation_id}


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    before: Optional[str] = None,
    current_user: TokenData = Depends(get_current_active_user)
):
    """获取对话消息列表"""
    conversation = _conversations_db.get(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    messages = _messages_db.get(conversation_id, [])
    
    # 如果指定了before参数，获取该消息之前的消息
    if before:
        found = False
        filtered = []
        for msg in reversed(messages):
            if msg["id"] == before:
                found = True
                continue
            if found:
                filtered.append(msg)
                if len(filtered) >= limit:
                    break
        messages = list(reversed(filtered))
    else:
        messages = messages[-limit:]
    
    return [MessageResponse(**msg) for msg in messages]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    发送消息并获取响应
    
    消息将通过编排代理处理：
    1. 意图识别
    2. 任务分解
    3. 代理调度
    4. LLM处理（自动RAG增强）
    5. 结果整合
    
    大模型服务(192.168.0.214:8802/chat/)会自动进行RAG检索增强
    """
    # 获取或创建对话
    conversation_id = request.conversation_id
    if not conversation_id:
        # 创建新对话
        conversation_id = str(uuid.uuid4())
        now = datetime.now()
        _conversations_db[conversation_id] = {
            "id": conversation_id,
            "user_id": current_user.user_id,
            "title": request.message[:50] + ("..." if len(request.message) > 50 else ""),
            "status": "active",
            "message_count": 0,
            "created_at": now,
            "updated_at": now
        }
        _messages_db[conversation_id] = []
    
    conversation = _conversations_db.get(conversation_id)
    if not conversation:
        # 当前项目使用内存存储，对话在服务重启后会丢失。
        # 为了提升前端体验：如果前端带着旧的 conversation_id 发来消息，这里自动重建对话而不是直接 404。
        now = datetime.now()
        _conversations_db[conversation_id] = {
            "id": conversation_id,
            "user_id": current_user.user_id,
            "title": request.message[:50] + ("..." if len(request.message) > 50 else ""),
            "status": "active",
            "message_count": 0,
            "created_at": now,
            "updated_at": now
        }
        _messages_db[conversation_id] = []
        conversation = _conversations_db[conversation_id]
    
    if conversation.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    messages = _messages_db.get(conversation_id, [])
    
    # 添加用户消息
    user_message_id = str(uuid.uuid4())
    user_message = {
        "id": user_message_id,
        "conversation_id": conversation_id,
        "role": "user",
        "content": request.message,
        "created_at": datetime.now()
    }
    messages.append(user_message)
    
    try:
        # 构建消息历史
        chat_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages[-20:]  # 保留最近20条消息作为上下文
        ]
        
        # 确定使用的代理
        agent_type = request.agent_type or "orchestrator"
        agent_used = agent_type
        
        # 如果指定了特定代理，直接调用
        if agent_type != "orchestrator":
            agent = agent_registry.get_agent(agent_type)
            if agent:
                # 创建任务上下文
                context = TaskContext(
                    task_id=str(uuid.uuid4()),
                    user_id=current_user.user_id,
                    conversation_id=conversation_id,
                    input=request.message,
                    metadata={"agent_type": agent_type}
                )
                result = await agent.execute(context)
                response_content = result.output.get("content", str(result.output)) if result.output else "处理失败"
            else:
                # 代理不存在，使用LLM直接处理
                response = await llm_service.chat(chat_messages)
                response_content = _extract_content(response)
        else:
            # 使用编排代理处理（智能分配专业代理）
            logger.info(f"使用编排代理处理消息: {request.message[:50]}...")
            orchestrator = agent_registry.orchestrator
            if orchestrator:
                try:
                    context = TaskContext(
                        task_id=str(uuid.uuid4()),
                        user_id=current_user.user_id,
                        conversation_id=conversation_id,
                        input=request.message,
                        metadata={"task_type": "chat"}
                    )
                    result = await orchestrator.execute(context)
                    
                    if result.success and result.output:
                        if isinstance(result.output, dict):
                            response_content = result.output.get("content", str(result.output))
                        else:
                            response_content = str(result.output)
                        agent_used = "orchestrator"
                        logger.info(f"编排代理响应成功: {response_content[:100]}...")
                    else:
                        # 编排失败，直接调用LLM
                        logger.warning(f"编排失败: {result.error}, 使用LLM直接处理")
                        response = await llm_service.chat(chat_messages)
                        response_content = _extract_content(response)
                        agent_used = "llm"
                except Exception as e:
                    logger.error(f"编排代理执行失败: {e}")
                    response = await llm_service.chat(chat_messages)
                    response_content = _extract_content(response)
                    agent_used = "llm"
            else:
                # 无编排代理，直接调用LLM
                logger.warning("无编排代理，使用LLM直接处理")
                response = await llm_service.chat(chat_messages)
                response_content = _extract_content(response)
                agent_used = "llm"
        
        # 计算token
        tokens = llm_service.count_messages_tokens(chat_messages)
        
        # 添加助手消息
        assistant_message_id = str(uuid.uuid4())
        assistant_message = {
            "id": assistant_message_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": response_content,
            "agent_type": agent_used,
            "tokens": tokens,
            "created_at": datetime.now()
        }
        messages.append(assistant_message)
        
        # 更新对话
        conversation["message_count"] = len(messages)
        conversation["updated_at"] = datetime.now()
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=MessageResponse(**assistant_message),
            agent_used=agent_used
        )
        
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    流式聊天接口
    
    返回SSE格式的流式响应
    """
    # 获取或创建对话
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        now = datetime.now()
        _conversations_db[conversation_id] = {
            "id": conversation_id,
            "user_id": current_user.user_id,
            "title": request.message[:50] + ("..." if len(request.message) > 50 else ""),
            "status": "active",
            "message_count": 0,
            "created_at": now,
            "updated_at": now
        }
        _messages_db[conversation_id] = []
    
    messages = _messages_db.get(conversation_id, [])
    
    # 添加用户消息
    user_message = {
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "role": "user",
        "content": request.message,
        "created_at": datetime.now()
    }
    messages.append(user_message)
    
    async def generate():
        """生成流式响应"""
        try:
            # 构建消息历史
            chat_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages[-20:]
            ]
            
            full_content = ""
            
            # 流式调用LLM
            async for chunk in llm_service.stream_chat(chat_messages):
                full_content += chunk
                yield f"data: {json.dumps({'content': chunk, 'conversation_id': conversation_id})}\n\n"
            
            # 添加助手消息
            assistant_message = {
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": full_content,
                "created_at": datetime.now()
            }
            messages.append(assistant_message)
            
            # 更新对话
            conversation = _conversations_db.get(conversation_id)
            if conversation:
                conversation["message_count"] = len(messages)
                conversation["updated_at"] = datetime.now()
            
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
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    发送消息到指定对话
    
    消息将通过编排代理处理，自动进行意图识别、任务分解、代理调度
    """
    conversation = _conversations_db.get(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")
    
    messages = _messages_db.get(conversation_id, [])
    
    # 添加用户消息
    user_message_id = str(uuid.uuid4())
    user_message = {
        "id": user_message_id,
        "conversation_id": conversation_id,
        "role": "user",
        "content": request.content,
        "created_at": datetime.now()
    }
    messages.append(user_message)
    
    try:
        # 构建消息历史
        chat_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages[-20:]
        ]
        
        # 调用LLM
        response = await llm_service.chat(chat_messages)
        response_content = _extract_content(response)
        
        # 计算token
        tokens = llm_service.count_messages_tokens(chat_messages)
        
        # 添加助手消息
        assistant_message_id = str(uuid.uuid4())
        assistant_message = {
            "id": assistant_message_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": response_content,
            "agent_type": request.agent_type,
            "tokens": tokens,
            "created_at": datetime.now()
        }
        messages.append(assistant_message)
        
        # 更新对话
        conversation["message_count"] = len(messages)
        conversation["updated_at"] = datetime.now()
        
        return MessageResponse(**assistant_message)
        
    except Exception as e:
        logger.error(f"消息处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """归档对话"""
    conversation = _conversations_db.get(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="无权操作此对话")
    
    conversation["status"] = "archived"
    conversation["updated_at"] = datetime.now()
    
    return {"message": "归档成功", "conversation_id": conversation_id}


@router.post("/{conversation_id}/optimize")
async def optimize_prompt(
    conversation_id: str,
    message_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    一键优化提示词
    
    使用学习代理优化用户输入的提示词
    """
    conversation = _conversations_db.get(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    messages = _messages_db.get(conversation_id, [])
    
    # 查找要优化的消息
    target_message = None
    for msg in messages:
        if msg["id"] == message_id and msg["role"] == "user":
            target_message = msg
            break
    
    if not target_message:
        raise HTTPException(status_code=404, detail="消息不存在或不是用户消息")
    
    # 使用学习代理优化提示词
    learning_agent = agent_registry.get_agent("learning")
    if learning_agent:
        context = TaskContext(
            task_id=str(uuid.uuid4()),
            user_id=current_user.user_id,
            conversation_id=conversation_id,
            input=target_message["content"],
            metadata={"task_type": "optimize_prompt"}
        )
        result = await learning_agent.execute(context)
        optimized_prompt = result.output.get("optimized_prompt", target_message["content"]) if result.output else target_message["content"]
    else:
        # 简单优化：添加医学上下文
        optimized_prompt = f"作为医学专家，请详细分析：{target_message['content']}"
    
    return {
        "original_prompt": target_message["content"],
        "optimized_prompt": optimized_prompt,
        "message_id": message_id
    }


# ============== 辅助函数 ==============

def _extract_content(response: Dict) -> str:
    """从LLM响应中提取内容"""
    if "choices" in response:
        return response["choices"][0].get("message", {}).get("content", "")
    elif "content" in response:
        return response["content"]
    else:
        return str(response)
