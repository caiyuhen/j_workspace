<<<<<<< HEAD
"""
FastAPI 中间件
- AuditLogMiddleware: 自动记录所有操作的稽查轨迹（21 CFR Part 11）
- RateLimitMiddleware: 接口限流
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import time
import json
from collections import defaultdict
from loguru import logger

from app.db.session import AsyncSessionLocal
from app.models.models import AuditLog


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    稽查日志中间件
    自动记录所有写操作（POST/PUT/PATCH/DELETE）的审计轨迹
    符合 FDA 21 CFR Part 11 要求
    """

    # 不需要记录的路径
    SKIP_PATHS = {"/health", "/", "/api/v1/openapi.json", "/api/v1/docs", "/api/v1/redoc"}
    # 只记录写操作
    LOG_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    # 审计日志中需要脱敏的字段
    SENSITIVE_FIELDS = {
        "password", "old_password", "new_password", "confirm_password",
        "token", "refresh_token", "authorization",
        "secret", "mfa_secret", "mfa_code", "smtp_password", "s3_secret_key"
    }

    async def dispatch(self, request: Request, call_next):
        # 避免在 response 生成后再去访问 DB Session 中 detach 的 user
        # 我们需要在进入路由前就尝试获取一些基本信息
        should_log = request.method in self.LOG_METHODS and request.url.path not in self.SKIP_PATHS
        default_new_values = None
        if should_log:
            # 兜底抓取请求体，避免只有少量模块手工设置 audit_new_values 的情况
            default_new_values = await self._extract_request_payload(request)
            if getattr(request.state, "audit_new_values", None) is None and default_new_values is not None:
                request.state.audit_new_values = default_new_values
            if getattr(request.state, "audit_resource_id", None) is None:
                request.state.audit_resource_id = self._infer_resource_id(request.url.path)

        response = await call_next(request)

        # 只记录写操作
        if not should_log:
            return response

        # 异步记录审计日志（不阻塞响应）
        try:
            await self._log_audit(request, response, default_new_values)
        except Exception as e:
            logger.error(f"审计日志记录失败: {e}")

        return response

    async def _log_audit(self, request: Request, response: Response, default_new_values=None):
        """异步写入审计日志"""
        user = getattr(request.state, "current_user", None)

        # 推断操作类型
        action = self._infer_action(request.method, request.url.path)
        module = self._infer_module(request.url.path)

        # 避免触发 lazy load 导致 greenlet_spawn 报错
        user_id = None
        username = "anonymous"
        user_role = None

        if user:
            # 显式使用 __dict__ 以防 SQLAlchemy 的 lazy load
            try:
                user_dict = user.__dict__
                user_id = user_dict.get('id')
                username = user_dict.get('username', "anonymous")
                user_role = str(user_dict.get('role_id')) if user_dict.get('role_id') else None
            except Exception as role_e:
                logger.debug(f"读取 user 属性失败: {role_e}")
                pass

        async with AsyncSessionLocal() as db:
            log = AuditLog(
                user_id=user_id,
                username=username,
                user_role=user_role,
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", "")[:500],
                action=action,
                module=module,
                resource_type=request.url.path,
                resource_id=getattr(request.state, "audit_resource_id", None) or self._infer_resource_id(request.url.path),
                old_values=getattr(request.state, "audit_old_values", None),
                new_values=getattr(request.state, "audit_new_values", None) or default_new_values,
                success=200 <= response.status_code < 400,
                error_message=getattr(request.state, "audit_error_message", None),
            )
            db.add(log)
            await db.commit()

    async def _extract_request_payload(self, request: Request):
        """提取并脱敏请求体，作为审计日志默认 new_values"""
        # 为避免读取请求体导致的挂起问题，临时禁用请求体的自动提取
        return None

    def _mask_sensitive(self, value):
        """递归脱敏敏感字段"""
        if isinstance(value, dict):
            masked = {}
            for k, v in value.items():
                key_lower = str(k).lower()
                if key_lower in self.SENSITIVE_FIELDS:
                    masked[k] = "***"
                else:
                    masked[k] = self._mask_sensitive(v)
            return masked
        if isinstance(value, list):
            return [self._mask_sensitive(v) for v in value]
        return value

    def _infer_resource_id(self, path: str):
        """从 URL 推断资源ID（通常是末段 UUID/数字）"""
        parts = [p for p in (path or "").split("/") if p]
        if not parts:
            return None
        last = parts[-1]
        if last in {"sign", "activate", "unblind", "upload", "assign"} and len(parts) >= 2:
            return parts[-2]
        if last in {"api", "v1"}:
            return None
        return last

    def _infer_action(self, method: str, path: str) -> str:
        mapping = {"POST": "CREATE", "PUT": "UPDATE", "PATCH": "UPDATE", "DELETE": "DELETE"}
        if "login" in path:
            return "LOGIN"
        if "logout" in path:
            return "LOGOUT"
        if "sign" in path or "esign" in path:
            return "SIGN"
        if "export" in path:
            return "EXPORT"
        return mapping.get(method, method)

    def _infer_module(self, path: str) -> str:
        parts = path.split("/")
        for p in parts:
            if p in {"trials", "patients", "users", "drugs", "contracts",
                     "documents", "visits", "adverse-events", "monitoring", "auth"}:
                if p == "drugs": return "/api/v1/drugs"
                return p.upper().replace("-", "_")
        return "SYSTEM"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简单的基于内存的限流中间件
    生产环境建议改用 Redis 分布式限流
    """
    def __init__(self, app, requests_per_minute: int = 300):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60  # 1分钟窗口

        # 清理过期记录
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < window
        ]

        if len(self._requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"code": 429, "message": "请求过于频繁，请稍后再试", "data": None}
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
=======
"""
FastAPI 中间件
- AuditLogMiddleware: 自动记录所有操作的稽查轨迹（21 CFR Part 11）
- RateLimitMiddleware: 接口限流
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import time
import json
from collections import defaultdict
from loguru import logger

from app.db.session import AsyncSessionLocal
from app.models.models import AuditLog


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    稽查日志中间件
    自动记录所有写操作（POST/PUT/PATCH/DELETE）的审计轨迹
    符合 FDA 21 CFR Part 11 要求
    """

    # 不需要记录的路径
    SKIP_PATHS = {"/health", "/", "/api/v1/openapi.json", "/api/v1/docs", "/api/v1/redoc"}
    # 只记录写操作
    LOG_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    # 审计日志中需要脱敏的字段
    SENSITIVE_FIELDS = {
        "password", "old_password", "new_password", "confirm_password",
        "token", "refresh_token", "authorization",
        "secret", "mfa_secret", "mfa_code", "smtp_password", "s3_secret_key"
    }

    async def dispatch(self, request: Request, call_next):
        # 避免在 response 生成后再去访问 DB Session 中 detach 的 user
        # 我们需要在进入路由前就尝试获取一些基本信息
        should_log = request.method in self.LOG_METHODS and request.url.path not in self.SKIP_PATHS
        default_new_values = None
        if should_log:
            # 兜底抓取请求体，避免只有少量模块手工设置 audit_new_values 的情况
            default_new_values = await self._extract_request_payload(request)
            if getattr(request.state, "audit_new_values", None) is None and default_new_values is not None:
                request.state.audit_new_values = default_new_values
            if getattr(request.state, "audit_resource_id", None) is None:
                request.state.audit_resource_id = self._infer_resource_id(request.url.path)

        response = await call_next(request)

        # 只记录写操作
        if not should_log:
            return response

        # 异步记录审计日志（不阻塞响应）
        try:
            await self._log_audit(request, response, default_new_values)
        except Exception as e:
            logger.error(f"审计日志记录失败: {e}")

        return response

    async def _log_audit(self, request: Request, response: Response, default_new_values=None):
        """异步写入审计日志"""
        user = getattr(request.state, "current_user", None)

        # 推断操作类型
        action = self._infer_action(request.method, request.url.path)
        module = self._infer_module(request.url.path)

        # 避免触发 lazy load 导致 greenlet_spawn 报错
        user_id = None
        username = "anonymous"
        user_role = None

        if user:
            # 显式使用 __dict__ 以防 SQLAlchemy 的 lazy load
            try:
                user_dict = user.__dict__
                user_id = user_dict.get('id')
                username = user_dict.get('username', "anonymous")
                user_role = str(user_dict.get('role_id')) if user_dict.get('role_id') else None
            except Exception as role_e:
                logger.debug(f"读取 user 属性失败: {role_e}")
                pass

        async with AsyncSessionLocal() as db:
            log = AuditLog(
                user_id=user_id,
                username=username,
                user_role=user_role,
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", "")[:500],
                action=action,
                module=module,
                resource_type=request.url.path,
                resource_id=getattr(request.state, "audit_resource_id", None) or self._infer_resource_id(request.url.path),
                old_values=getattr(request.state, "audit_old_values", None),
                new_values=getattr(request.state, "audit_new_values", None) or default_new_values,
                success=200 <= response.status_code < 400,
                error_message=getattr(request.state, "audit_error_message", None),
            )
            db.add(log)
            await db.commit()

    async def _extract_request_payload(self, request: Request):
        """提取并脱敏请求体，作为审计日志默认 new_values"""
        # 为避免读取请求体导致的挂起问题，临时禁用请求体的自动提取
        return None

    def _mask_sensitive(self, value):
        """递归脱敏敏感字段"""
        if isinstance(value, dict):
            masked = {}
            for k, v in value.items():
                key_lower = str(k).lower()
                if key_lower in self.SENSITIVE_FIELDS:
                    masked[k] = "***"
                else:
                    masked[k] = self._mask_sensitive(v)
            return masked
        if isinstance(value, list):
            return [self._mask_sensitive(v) for v in value]
        return value

    def _infer_resource_id(self, path: str):
        """从 URL 推断资源ID（通常是末段 UUID/数字）"""
        parts = [p for p in (path or "").split("/") if p]
        if not parts:
            return None
        last = parts[-1]
        if last in {"sign", "activate", "unblind", "upload", "assign"} and len(parts) >= 2:
            return parts[-2]
        if last in {"api", "v1"}:
            return None
        return last

    def _infer_action(self, method: str, path: str) -> str:
        mapping = {"POST": "CREATE", "PUT": "UPDATE", "PATCH": "UPDATE", "DELETE": "DELETE"}
        if "login" in path:
            return "LOGIN"
        if "logout" in path:
            return "LOGOUT"
        if "sign" in path or "esign" in path:
            return "SIGN"
        if "export" in path:
            return "EXPORT"
        return mapping.get(method, method)

    def _infer_module(self, path: str) -> str:
        parts = path.split("/")
        for p in parts:
            if p in {"trials", "patients", "users", "drugs", "contracts",
                     "documents", "visits", "adverse-events", "monitoring", "auth"}:
                if p == "drugs": return "/api/v1/drugs"
                return p.upper().replace("-", "_")
        return "SYSTEM"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简单的基于内存的限流中间件
    生产环境建议改用 Redis 分布式限流
    """
    def __init__(self, app, requests_per_minute: int = 300):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60  # 1分钟窗口

        # 清理过期记录
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < window
        ]

        if len(self._requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"code": 429, "message": "请求过于频繁，请稍后再试", "data": None}
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
>>>>>>> origin/main
