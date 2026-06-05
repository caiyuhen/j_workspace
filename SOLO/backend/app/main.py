"""
医学智能体协同系统 - FastAPI主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1 import conversations, agents, skills, auth
from app.agents.registry import agent_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    print(f"📡 LLM服务: {settings.LLM_ENDPOINT}")
    print(f"🤖 已注册代理: {agent_registry.list_agents()}")
    
    yield
    
    # 关闭时清理
    print("👋 应用关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    医学专业智能体协同系统 API
    
    ## 核心特性
    - 多代理协同架构
    - 大模型服务内置RAG（192.168.0.214:8802/chat/）
    - Skill集成（skillhub.cn + MCP）
    """,
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(
    conversations.router,
    prefix="/api/v1/conversations",
    tags=["对话管理"]
)

app.include_router(
    agents.router,
    prefix="/api/v1/agents",
    tags=["代理管理"]
)

app.include_router(
    skills.router,
    prefix="/api/v1/skills",
    tags=["Skill管理"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["认证管理"]
)


@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "llm_endpoint": settings.LLM_ENDPOINT,
        "agents": agent_registry.list_agents()
    }
