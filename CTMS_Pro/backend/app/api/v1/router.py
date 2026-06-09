<<<<<<< HEAD
"""
API 路由总线 - 汇总所有子路由
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    trials,
    patients,
    visits,
    adverse_events,
    drugs,
    contracts,
    documents,
    monitoring,
    reports,
    notifications,
    iwrs,
    sites,
    timesheets,
)

api_router = APIRouter()

# ─── 认证 ────────────────────────────────────────────────────
api_router.include_router(auth.router, prefix="/auth", tags=["🔐 认证"])

# ─── 用户管理 ─────────────────────────────────────────────────
api_router.include_router(users.router, prefix="/users", tags=["👤 用户管理"])

# ─── 机构/中心管理 ─────────────────────────────────────────────
api_router.include_router(sites.router, prefix="/sites", tags=["🏢 机构/中心管理"])

# ─── 工时管理 ─────────────────────────────────────────────
api_router.include_router(timesheets.router, prefix="/timesheets", tags=["⏱️ 工时管理"])

# ─── 试验管理 ─────────────────────────────────────────────────
api_router.include_router(trials.router, prefix="/trials", tags=["🔬 试验管理"])

# ─── 患者管理 ─────────────────────────────────────────────────
api_router.include_router(patients.router, prefix="/patients", tags=["👥 患者管理"])

# ─── 访视管理 ─────────────────────────────────────────────────
api_router.include_router(visits.router, prefix="/visits", tags=["📅 访视管理"])

# ─── SAE / 不良事件 ───────────────────────────────────────────
api_router.include_router(adverse_events.router, prefix="/adverse-events", tags=["⚠️ SAE管理"])

# ─── 药品管理 ─────────────────────────────────────────────────
api_router.include_router(drugs.router, prefix="/drugs", tags=["💊 药品管理"])

# ─── 经费管理 ─────────────────────────────────────────────────
api_router.include_router(contracts.router, prefix="/contracts", tags=["💰 经费管理"])

# ─── 文档 / eTMF ──────────────────────────────────────────────
api_router.include_router(documents.router, prefix="/documents", tags=["🗄️ eTMF文档"])

# ─── 质控 / 监查 ──────────────────────────────────────────────
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["✅ 质控监查"])

# ─── 统计报表 ─────────────────────────────────────────────────
api_router.include_router(reports.router, prefix="/reports", tags=["📊 统计报表"])

# ─── 通知 ─────────────────────────────────────────────────────
api_router.include_router(notifications.router, prefix="/notifications", tags=["🔔 通知消息"])

# ─── IWRS 随机化系统 ─────────────────────────────────────────────
api_router.include_router(iwrs.router, tags=["🎲 IWRS随机化"])
=======
"""
API 路由总线 - 汇总所有子路由
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    trials,
    patients,
    visits,
    adverse_events,
    drugs,
    contracts,
    documents,
    monitoring,
    reports,
    notifications,
    iwrs,
    sites,
    timesheets,
)

api_router = APIRouter()

# ─── 认证 ────────────────────────────────────────────────────
api_router.include_router(auth.router, prefix="/auth", tags=["🔐 认证"])

# ─── 用户管理 ─────────────────────────────────────────────────
api_router.include_router(users.router, prefix="/users", tags=["👤 用户管理"])

# ─── 机构/中心管理 ─────────────────────────────────────────────
api_router.include_router(sites.router, prefix="/sites", tags=["🏢 机构/中心管理"])

# ─── 工时管理 ─────────────────────────────────────────────
api_router.include_router(timesheets.router, prefix="/timesheets", tags=["⏱️ 工时管理"])

# ─── 试验管理 ─────────────────────────────────────────────────
api_router.include_router(trials.router, prefix="/trials", tags=["🔬 试验管理"])

# ─── 患者管理 ─────────────────────────────────────────────────
api_router.include_router(patients.router, prefix="/patients", tags=["👥 患者管理"])

# ─── 访视管理 ─────────────────────────────────────────────────
api_router.include_router(visits.router, prefix="/visits", tags=["📅 访视管理"])

# ─── SAE / 不良事件 ───────────────────────────────────────────
api_router.include_router(adverse_events.router, prefix="/adverse-events", tags=["⚠️ SAE管理"])

# ─── 药品管理 ─────────────────────────────────────────────────
api_router.include_router(drugs.router, prefix="/drugs", tags=["💊 药品管理"])

# ─── 经费管理 ─────────────────────────────────────────────────
api_router.include_router(contracts.router, prefix="/contracts", tags=["💰 经费管理"])

# ─── 文档 / eTMF ──────────────────────────────────────────────
api_router.include_router(documents.router, prefix="/documents", tags=["🗄️ eTMF文档"])

# ─── 质控 / 监查 ──────────────────────────────────────────────
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["✅ 质控监查"])

# ─── 统计报表 ─────────────────────────────────────────────────
api_router.include_router(reports.router, prefix="/reports", tags=["📊 统计报表"])

# ─── 通知 ─────────────────────────────────────────────────────
api_router.include_router(notifications.router, prefix="/notifications", tags=["🔔 通知消息"])

# ─── IWRS 随机化系统 ─────────────────────────────────────────────
api_router.include_router(iwrs.router, tags=["🎲 IWRS随机化"])
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
