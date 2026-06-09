# CTMS Pro - 部署与开发文档

## 技术栈

| 层次 | 技术 | 版本 |
|------|------|------|
| 前端 | HTML5 + CSS3 + Vanilla JS | - |
| 后端框架 | FastAPI (Python) | 0.111 |
| 数据库 | PostgreSQL | 15 |
| 缓存 | Redis | 7 |
| 文件存储 | MinIO (S3兼容) | Latest |
| 反向代理 | Nginx | Alpine |
| 容器化 | Docker + Docker Compose | 3.9 |
| ORM | SQLAlchemy (异步) | 2.0 |
| 认证 | JWT (python-jose) + Fernet加密 | - |

---

## 快速启动（Docker方式）

```bash
# 1. 克隆项目
cd d:/workspace/CTMS_Pro

# 2. 复制环境配置
copy backend\.env.example backend\.env
# 编辑 .env 修改数据库密码、SECRET_KEY 等

# 3. 一键启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看后端日志
docker-compose logs -f backend
```

启动后访问：
- **前端**: http://localhost
- **API文档 (Swagger)**: http://localhost/api/v1/docs
- **API文档 (ReDoc)**: http://localhost/api/v1/redoc
- **MinIO控制台**: http://localhost:9001 (admin/minioadmin123)

---

## 本地开发启动

### 前提条件
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 步骤

```bash
# 1. 进入后端目录
cd d:/workspace/CTMS_Pro/backend

# 2. 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
# 先在 PostgreSQL 中创建数据库：
# CREATE DATABASE ctms_pro;
# CREATE USER ctms_user WITH PASSWORD 'ctms_password_2026';
# GRANT ALL PRIVILEGES ON DATABASE ctms_pro TO ctms_user;

# 执行 DDL 脚本
psql -U ctms_user -d ctms_pro -f ../database/init/01_schema.sql

# 5. 复制环境配置
copy .env.example .env

# 6. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. 启动前端（另开终端）
cd d:/workspace/CTMS_Pro
python -m http.server 8899
```

---

## 项目结构

```
CTMS_Pro/
├── index.html                     # 前端入口
├── assets/
│   ├── css/main.css               # 全局样式
│   └── js/
│       ├── api-client.js          # ★ 后端API客户端
│       ├── app.js                 # 应用核心/路由
│       ├── data.js                # 模拟数据 (fallback)
│       ├── login.js               # 登录页面
│       ├── pages-trials.js        # 试验相关页面
│       ├── pages-patients.js      # 患者相关页面
│       └── pages-others.js        # 其他功能页面
│
├── backend/                       # ★ Python FastAPI 后端
│   ├── app/
│   │   ├── main.py                # 应用入口
│   │   ├── core/
│   │   │   ├── config.py          # 配置管理
│   │   │   ├── security.py        # JWT/加密/密码
│   │   │   ├── dependencies.py    # RBAC权限依赖
│   │   │   ├── middleware.py      # 审计日志/限流中间件
│   │   │   └── logging.py         # 日志配置
│   │   ├── db/
│   │   │   ├── session.py         # 数据库会话
│   │   │   └── init_db.py         # 初始化超管
│   │   ├── models/
│   │   │   └── models.py          # SQLAlchemy ORM模型
│   │   └── api/v1/
│   │       ├── router.py          # 路由汇总
│   │       └── endpoints/
│   │           ├── auth.py        # 登录/登出/Token
│   │           ├── users.py       # 用户管理
│   │           ├── trials.py      # 试验管理
│   │           ├── patients.py    # 患者管理+eICF
│   │           ├── visits.py      # 访视管理
│   │           ├── adverse_events.py  # SAE管理
│   │           ├── drugs.py       # 药品管理
│   │           ├── contracts.py   # 经费管理
│   │           ├── monitoring.py  # 质控监查
│   │           ├── documents.py   # eTMF文档
│   │           ├── reports.py     # 统计报表+稽查轨迹
│   │           └── notifications.py  # 通知消息
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── database/
│   └── init/
│       └── 01_schema.sql          # ★ PostgreSQL 完整建表SQL
│
├── nginx/
│   ├── nginx.conf
│   └── conf.d/ctms.conf
│
└── docker-compose.yml             # ★ 一键部署配置
```

---

## 数据库说明（中心维度）

- SQL入口：`database/init/01_schema.sql`（版本 `1.1.0`）
- 中心分层策略：
  - `trial_milestones.site_id`：`NULL` 表示项目级，非 `NULL` 表示中心级里程碑
  - `adverse_events.site_id`：SAE直接归属中心，便于按中心统计和查询
  - `monitoring_reports.site_id`：质控记录归属中心
  - `documents.site_id`：eTMF 文档归属中心
- 兼容性：
  - 脚本内包含 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，可用于已有数据库平滑补字段
- 关键索引（中心组查询）：
  - `idx_trial_milestones_trial_site_date`
  - `idx_adverse_events_trial_site_created`
  - `idx_monitoring_reports_trial_site_date`
  - `idx_documents_trial_site_type_created`

---

## API 接口清单

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | /auth/login | 登录 |
| 认证 | POST | /auth/logout | 登出 |
| 认证 | POST | /auth/refresh | 刷新Token |
| 认证 | GET | /auth/me | 当前用户 |
| 认证 | PUT | /auth/change-password | 修改密码 |
| 用户 | GET/POST | /users | 用户列表/创建 |
| 用户 | GET/PUT | /users/{id} | 用户详情/更新 |
| 用户 | GET | /users/roles | 角色列表 |
| 试验 | GET/POST | /trials | 试验列表/创建 |
| 试验 | GET/PUT/DEL | /trials/{id} | 试验CRUD |
| 试验 | GET | /trials/statistics | 统计概览 |
| 试验 | GET/POST | /trials/{id}/milestones | 里程碑 |
| 患者 | GET/POST | /patients | 患者列表/创建 |
| 患者 | GET/PUT | /patients/{id} | 患者详情/更新 |
| 患者 | POST | /patients/{id}/econsent | 发起知情同意 |
| 患者 | POST | /patients/{id}/econsent/{id}/sign | 签署eICF |
| 访视 | GET/POST | /visits | 访视列表/创建 |
| 访视 | GET | /visits/upcoming | 近期访视 |
| SAE | GET/POST | /adverse-events | AE列表/上报 |
| SAE | GET/PUT | /adverse-events/{id} | AE详情/更新 |
| 药品 | GET/POST | /drugs/batches | 批次列表/入库 |
| 药品 | POST | /drugs/dispense | 发放 |
| 药品 | POST | /drugs/return | 回收 |
| 经费 | GET/POST | /contracts/contracts | 合同管理 |
| 经费 | GET/POST | /contracts/payments | 付款管理 |
| 质控 | GET/POST | /monitoring/reports | 监查报告 |
| 质控 | GET/POST/PUT | /monitoring/issues | 质控问题 |
| 文档 | GET/POST | /documents | eTMF文档 |
| 文档 | POST | /documents/{id}/sign | 电子签名 |
| 报表 | GET | /reports/dashboard | Dashboard统计 |
| 报表 | GET | /reports/enrollment-trend | 入组趋势 |
| 报表 | GET | /reports/audit-logs | 稽查轨迹 |

---

## 合规说明

| 法规 | 实现方式 |
|------|----------|
| **FDA 21 CFR Part 11** | JWT电子签名、完整稽查轨迹（audit_logs表）、PKI签名接口 |
| **GDPR** | PII字段AES-256加密存储、数据最小化、GDPR操作日志 |
| **HIPAA** | 患者数据加密、最小权限原则、访问日志 |
| **GCP E6(R2)** | eTMF分类结构、文档版本控制、合规检查 |
| **ISO 27001** | RBAC权限控制、账号锁定、TLS传输加密 |

---

## 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 超级管理员 | admin@ctms-pro.com | Admin@CTMS2026! |

> ⚠️ 生产部署前请立即修改默认密码！
