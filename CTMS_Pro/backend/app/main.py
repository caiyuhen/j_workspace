<<<<<<< HEAD
"""
CTMS Pro - FastAPI 主应用入口
Clinical Trial Management System
符合 GCP / FDA 21 CFR Part 11 / GDPR 合规标准
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import uuid
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, Base
from app.api.v1.router import api_router
from app.core.middleware import AuditLogMiddleware, RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    setup_logging()
    logger.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"   环境: {settings.APP_ENV}")
    logger.info(f"   数据库: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

    # 初始化数据库连接池
    async with engine.begin() as conn:
        # 在开发环境自动创建表（生产环境用 Alembic）
        if settings.APP_ENV == "development":
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ 数据库表初始化完成")

    # 初始化超管账号
    from app.db.init_db import init_db
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await init_db(session)

    yield

    logger.info("🛑 CTMS Pro 正在关闭...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## CTMS Pro - 临床试验管理系统 API

    ### 合规标准
    - ✅ ICH GCP E6(R2)
    - ✅ FDA 21 CFR Part 11 (电子签名 / 审计轨迹)
    - ✅ GDPR (数据保护)
    - ✅ HIPAA (患者隐私)
    - ✅ ISO 27001 (信息安全)

    ### 认证方式
    使用 **Bearer Token (JWT)** 认证，在请求头中携带：
    ```
    Authorization: Bearer <access_token>
    ```
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# ─── 安全中间件 ──────────────────────────────────────────
# 使用动态返回 Origin 的方式，彻底解决跨域凭证冲突
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",  # 允许所有 Origin 并动态回显，解决 localhost/127.0.0.1 及 IP 访问时的跨域问题
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(AuditLogMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=300)


# ─── 请求追踪中间件 ───────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


# ─── 全局异常处理 ─────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": f"服务器内部错误: {str(exc)}", "data": None},
    )


# ─── 注册路由 ─────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ─── 健康检查 ─────────────────────────────────────────────
@app.get("/health", tags=["系统"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


@app.get("/", tags=["系统"])
async def root():
    return {
        "message": "CTMS Pro API 服务运行中",
        "docs": f"{settings.API_V1_STR}/docs",
        "version": settings.APP_VERSION,
    }
=======
"""
CTMS Pro - FastAPI 主应用入口
Clinical Trial Management System
符合 GCP / FDA 21 CFR Part 11 / GDPR 合规标准
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import uuid
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, Base
from app.api.v1.router import api_router
from app.core.middleware import AuditLogMiddleware, RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    setup_logging()
    logger.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"   环境: {settings.APP_ENV}")
    logger.info(f"   数据库: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

    # 初始化数据库连接池
    async with engine.begin() as conn:
        # 在开发环境自动创建表（生产环境用 Alembic）
        if settings.APP_ENV == "development":
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ 数据库表初始化完成")

    # 初始化超管账号
    from app.db.init_db import init_db
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await init_db(session)

    yield

    logger.info("🛑 CTMS Pro 正在关闭...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## CTMS Pro - 临床试验管理系统 API

    ### 合规标准
    - ✅ ICH GCP E6(R2)
    - ✅ FDA 21 CFR Part 11 (电子签名 / 审计轨迹)
    - ✅ GDPR (数据保护)
    - ✅ HIPAA (患者隐私)
    - ✅ ISO 27001 (信息安全)

    ### 认证方式
    使用 **Bearer Token (JWT)** 认证，在请求头中携带：
    ```
    Authorization: Bearer <access_token>
    ```
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# ─── 安全中间件 ──────────────────────────────────────────
# 使用动态返回 Origin 的方式，彻底解决跨域凭证冲突
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",  # 允许所有 Origin 并动态回显，解决 localhost/127.0.0.1 及 IP 访问时的跨域问题
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(AuditLogMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=300)


# ─── 请求追踪中间件 ───────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


# ─── 全局异常处理 ─────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": f"服务器内部错误: {str(exc)}", "data": None},
    )


# ─── 注册路由 ─────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ─── 健康检查 ─────────────────────────────────────────────
@app.get("/health", tags=["系统"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }


@app.get("/", tags=["系统"])
async def root():
    return {
        "message": "CTMS Pro API 服务运行中",
        "docs": f"{settings.API_V1_STR}/docs",
        "version": settings.APP_VERSION,
    }
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
