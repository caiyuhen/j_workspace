# CTMS Pro

## 项目概述

CTMS Pro 是一个临床试验管理系统，当前仓库的实际形态为：

- 静态前端：`index.html` + `assets/js/*.js`
- FastAPI 后端：`backend/app/main.py`
- PostgreSQL：核心业务数据
- Redis：缓存与令牌/任务相关依赖
- MinIO：文档对象存储
- Nginx：前端静态托管与 `/api/` 反向代理
- Celery Worker：当前仅保留占位容器，异步任务链路未正式启用

README 以下内容以当前仓库落盘代码与 `docker-compose.yml` 为准。

---

## 功能说明

### 1. 用户与权限管理

- 核心能力：
  - 支持用户名或邮箱登录，登录成功后返回 `access_token`、`refresh_token`、过期时间和当前用户信息
  - 支持登出、刷新令牌、修改密码，满足日常会话续期与账户维护需求
  - 支持基于角色的 RBAC 权限控制，后端通过依赖注入限制不同角色的可访问资源
  - 支持登录失败次数累计与锁定策略，连续失败达到阈值后暂时锁定账号
  - 支持认证相关审计日志，记录登录成功、失败、登出等关键行为
- 关键数据对象：
  - `users`
  - `roles`
  - `token_blacklist`
  - `audit_logs`
- 典型流程：
  - 管理员创建用户并分配角色
  - 用户登录后获取 Bearer Token
  - 业务接口根据角色判断访问权限
  - 登出后令牌进入黑名单并立即失效
- 适用场景：
  - 超级管理员统一管理平台账号
  - 研究者、协调员、药管、监查员按角色访问模块

### 2. 试验项目管理

- 核心能力：
  - 支持试验基本信息创建、查询、更新与删除
  - 支持试验统计概览，汇总项目数量、状态和执行指标
  - 支持里程碑管理，并区分项目级与中心级里程碑
  - 支持按试验维度聚合患者、中心、药品、AE、文档、监查等业务数据
- 关键数据对象：
  - `trials`
  - `trial_sites`
  - `trial_milestones`
- 典型流程：
  - 立项后创建试验主档
  - 绑定参与中心
  - 为项目配置关键里程碑与执行计划
  - 后续各业务模块均以试验 ID 为主线进行关联
- 适用场景：
  - 管理临床试验主档案
  - 跟踪项目进度、关键节点和中心执行情况

### 3. 中心与组织管理

- 核心能力：
  - 支持中心信息创建、编辑、删除和查询
  - 支持组织、中心、试验之间的层级化管理
  - 支持中心维度的数据归集，包括 AE、监查、文档、里程碑和入组等
- 关键数据对象：
  - `sites`
  - `organizations`
  - `trial_sites`
- 典型流程：
  - 先建立组织与中心主数据
  - 再将中心挂接到具体试验
  - 在后续报表与业务查询中按中心维度聚合展示
- 适用场景：
  - 多中心项目统一协调
  - 按中心查看入组、监查、文档和问题

### 4. 患者与 eConsent 管理

- 核心能力：
  - 支持患者基本信息录入、更新、查询和统计
  - 支持患者与试验、中心、访视之间的主数据关联
  - 支持电子知情同意发起、签署和留痕
  - 支持患者管理与试验执行链路打通，便于统一跟踪受试者状态
- 关键数据对象：
  - `patients`
  - `econsents`
- 典型流程：
  - 录入受试者基础信息并关联试验/中心
  - 发起 eConsent
  - 完成电子签署后进入后续访视和随机化流程
- 适用场景：
  - 受试者招募与随访管理
  - 电子知情同意留痕

### 5. 访视管理

- 核心能力：
  - 支持访视创建、查询和按条件筛选
  - 支持近期访视提醒视图，便于查看即将到期的任务
  - 支持按患者、试验、中心维度组织访视记录
- 关键数据对象：
  - `patient_visits`
- 典型流程：
  - 根据试验方案建立访视计划
  - 录入实际访视执行信息
  - 通过近期访视接口查看待执行事项
- 适用场景：
  - 跟踪受试者访视计划
  - 快速查看即将到期或待执行访视

### 6. SAE / AE 管理

- 核心能力：
  - 支持不良事件录入、更新和详情查询
  - 支持 AE 统计接口，按项目或中心汇总风险情况
  - 支持按试验、中心、时间维度检索安全性事件
- 关键数据对象：
  - `adverse_events`
- 典型流程：
  - 发生 AE/SAE 后录入事件
  - 更新严重程度、处理措施和状态
  - 在报表层面做安全性趋势分析
- 适用场景：
  - SAE/AE 上报
  - 安全性事件分析与追踪

### 7. 药品管理

- 核心能力：
  - 支持药品批次入库与批次信息维护
  - 支持药品发放与回收
  - 支持药品日志查询和库存汇总
- 关键数据对象：
  - `drug_batches`
  - `drug_dispensing`
  - `drug_returns`
- 典型流程：
  - 建立药品批次
  - 按受试者或中心执行发药
  - 回收剩余药品并汇总库存变化
- 适用场景：
  - 试验用药批次管理
  - 发药、回收、库存核对

### 8. 经费与合同管理

- 核心能力：
  - 支持合同管理
  - 支持付款管理
  - 支持预算汇总与执行跟踪
- 关键数据对象：
  - `contracts`
  - `payments`
- 典型流程：
  - 建立项目合同
  - 录入付款节点与金额
  - 通过预算汇总接口查看合同执行情况
- 适用场景：
  - 项目预算执行跟踪
  - 合同与付款进度管理

### 9. 文档与 eTMF 管理

- 核心能力：
  - 支持文档记录创建、查询与按中心/试验归档
  - 支持文档电子签名
  - 支持 MinIO 作为对象存储底座
- 关键数据对象：
  - `documents`
- 典型流程：
  - 创建文档记录并关联试验/中心
  - 进入签署环节
  - 后续通过文档清单和签署状态进行追踪
- 当前说明：
  - 当前后端已具备文档元数据与签署能力
  - 完整文件上传链路在当前仓库中未完整暴露为独立公开接口
  - 因此当前更适合将该模块理解为“文档记录与签署管理”，而不是完整 DMS

### 10. 监查与质控

- 核心能力：
  - 支持监查报告管理
  - 支持质控问题管理
  - 支持删除监查报告
- 关键数据对象：
  - `monitoring_reports`
  - `qc_issues`
- 典型流程：
  - CRA/QA 提交监查报告
  - 形成质控问题
  - 跟踪整改状态直至关闭
- 适用场景：
  - CRA/QA 记录监查结果
  - 跟踪问题整改闭环

### 11. 统计报表

- 核心能力：
  - 支持 Dashboard 概览
  - 支持入组趋势报表
  - 支持中心入组报表
  - 支持 AE 汇总报表
  - 支持审计日志查询
- 输出价值：
  - 为项目管理层提供执行态势总览
  - 为监查、质控和运营提供量化依据
  - 为审计追踪提供事件明细查询能力
- 适用场景：
  - 项目执行态势总览
  - 中心入组、安全性与审计分析

### 12. 通知消息

- 核心能力：
  - 支持通知列表查询
  - 支持单条已读
  - 支持全部已读
- 典型用途：
  - 待办提醒
  - 系统广播
  - 操作结果反馈
- 适用场景：
  - 系统提醒
  - 待办消息确认

### 13. IWRS 随机化

- 核心能力：
  - 支持随机方案管理
  - 支持方案激活
  - 支持受试者随机分配
  - 支持随机化记录查询
  - 支持紧急揭盲
  - 支持方案统计
- 关键数据对象：
  - `randomization_schemes`
  - `subject_randomizations`
  - `randomization_codes`
- 典型流程：
  - 建立随机化方案
  - 激活方案并导入随机码
  - 对受试者执行随机分配
  - 必要时执行揭盲并保留审计记录
- 适用场景：
  - 临床试验随机化分组
  - 受试者分配与揭盲追踪

### 14. 审计与安全

- 核心能力：
  - 支持请求级审计中间件
  - 支持请求 ID 与处理耗时响应头
  - 支持全局异常处理
  - 支持 Trusted Host 与基础限流
- 当前价值：
  - 为问题排查提供链路追踪信息
  - 为合规审计提供基础日志能力
  - 为生产环境提供最基础的防护措施
- 适用场景：
  - 合规审计
  - 问题排查
  - 安全控制

---

## 技术栈

| 层次 | 技术 | 备注 |
|------|------|------|
| 前端 | HTML5 + CSS3 + Vanilla JS | 单页式静态前端 |
| 后端 | FastAPI + Uvicorn | OpenAPI 文档自动生成 |
| ORM | SQLAlchemy Async | `asyncpg` 驱动 |
| 数据库 | PostgreSQL 15 | Docker 默认容器名 `ctms_postgres` |
| 缓存 | Redis 7 | 当前密码为空 |
| 文件存储 | MinIO | S3 兼容 |
| 反向代理 | Nginx | 前端与 API 同源代理 |
| 容器化 | Docker Compose 3.9 | 根目录 `docker-compose.yml` |
| 认证 | JWT Access/Refresh | Bearer Token |

---

## 实际访问地址

### Docker 部署后

- 前端首页：`http://localhost:8811`
- 后端直连：`http://localhost:8898`
- Swagger：`http://localhost:8898/api/v1/docs`
- ReDoc：`http://localhost:8898/api/v1/redoc`
- Nginx 代理下的 Swagger：`http://localhost:8811/api/v1/docs`
- MinIO API：`http://localhost:7000`
- MinIO Console：`http://localhost:7001`

### 说明

- Docker 中后端容器内部监听端口是 `8443`，宿主机映射为 `8898`
- Nginx 对外暴露 `8811:80`，并将 `/api/` 反代到后端
- README 旧版本中写的 `http://localhost`、`9001` 等地址已不再对应当前 Compose 配置

---

## Docker 快速启动

### 启动步骤

```bash
cd /home/user/CTMS_Pro
docker compose up -d
docker compose ps
docker compose logs -f backend
```

### 默认启动服务

- `postgres`
- `redis`
- `minio`
- `backend`
- `nginx`
- `celery_worker`

### 注意事项

- `celery_worker` 当前是占位容器，命令只会打印 “Celery is temporarily disabled because worker.py is missing”
- `database/init/` 会在 PostgreSQL 首次启动时自动执行
- 如果你需要重建镜像，请使用：

```bash
docker compose up -d --build
```

---

## 本地开发启动

### 前提条件

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 后端启动

```bash
cd /home/user/CTMS_Pro/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8898
```

### 初始化数据库

```bash
createdb ctms_pro
psql -U ctms_user -d ctms_pro -f ../database/init/01_schema.sql
```

### 前端启动

```bash
cd /home/user/CTMS_Pro
python -m http.server 8899
```

### 本地开发口径说明

- 当前前端 `assets/js/api-client.js` 在端口 `8899` 下会默认请求 `http://127.0.0.1:8898/api/v1`
- 因此本地开发时，推荐后端跑在 `8898` 而不是旧文档里的 `8000`
- 如果你坚持让后端跑在其他端口，需要手动在浏览器 `localStorage` 中设置 `ctms_api_base`

---

## 项目结构

```text
CTMS_Pro/
├── index.html
├── assets/
│   ├── css/main.css
│   └── js/
│       ├── api-client.js
│       ├── app.js
│       ├── data.js
│       ├── login.js
│       ├── pages-trials.js
│       ├── pages-patients.js
│       └── pages-others.js
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── dependencies.py
│   │   │   ├── middleware.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   ├── models/models.py
│   │   ├── services/
│   │   └── api/v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── users.py
│   │           ├── sites.py
│   │           ├── timesheets.py
│   │           ├── trials.py
│   │           ├── patients.py
│   │           ├── visits.py
│   │           ├── adverse_events.py
│   │           ├── drugs.py
│   │           ├── contracts.py
│   │           ├── documents.py
│   │           ├── monitoring.py
│   │           ├── reports.py
│   │           ├── notifications.py
│   │           └── iwrs.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── database/init/01_schema.sql
├── nginx/
│   ├── nginx.conf
│   └── conf.d/ctms.conf
├── docker-compose.yml
├── create_trial_extensions.sql
└── tests/
```

---

## 当前后端模块

所有 API 统一挂在前缀：

```text
/api/v1
```

当前注册的模块包括：

- 认证：`/auth`
- 用户管理：`/users`
- 机构/中心管理：`/sites`
- 工时管理：`/timesheets`
- 试验管理：`/trials`
- 患者管理：`/patients`
- 访视管理：`/visits`
- 不良事件：`/adverse-events`
- 药品管理：`/drugs`
- 经费管理：`/contracts`
- 文档/eTMF：`/documents`
- 质控监查：`/monitoring`
- 报表：`/reports`
- 通知：`/notifications`
- IWRS：`/iwrs/*`

---

## 认证说明

### 登录接口

当前登录接口为：

```text
POST /api/v1/auth/login
```

请求体为 JSON，不是 OAuth2 form：

```json
{
  "username": "admin@ctms-pro.com",
  "password": "Admin@CTMS2026!"
}
```

登录成功返回：

- `access_token`
- `refresh_token`
- `token_type`
- `expires_in`
- `user`

后续接口通过 Bearer Token 访问：

```http
Authorization: Bearer <access_token>
```

### 当前认证实现包含

- Access Token + Refresh Token 双令牌
- 登出后 Token 黑名单失效
- 连续密码错误 5 次锁定 30 分钟
- 密码强度校验
- RBAC 权限控制
- 启动时自动初始化默认超管

### 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 超级管理员 | `admin@ctms-pro.com` | `Admin@CTMS2026!` |

> 生产环境必须立即修改默认密码与 `SECRET_KEY`

### 开发测试说明

认证代码中当前存在一个仅用于开发测试的 IWRS mock 登录分支：

- 用户名：`IWRS@iwrs.com`
- 密码：`I@123`

该逻辑不建议在生产环境保留。

---

## API 接口概览

### 认证

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `PUT /api/v1/auth/change-password`

### 用户与中心

- `GET/POST /api/v1/users`
- `GET/PUT /api/v1/users/{id}`
- `GET /api/v1/users/roles`
- `GET/POST /api/v1/sites`
- `GET/PUT/DELETE /api/v1/sites/{id}`

### 工时与试验

- `GET/POST /api/v1/timesheets`
- `GET/PUT/DELETE /api/v1/timesheets/{id}`
- `GET/POST /api/v1/trials`
- `GET/PUT/DELETE /api/v1/trials/{id}`
- `GET /api/v1/trials/statistics`
- `GET/POST /api/v1/trials/{id}/milestones`

### 患者与访视

- `GET/POST /api/v1/patients`
- `GET/PUT /api/v1/patients/{id}`
- `GET /api/v1/patients/statistics`
- `POST /api/v1/patients/{id}/econsent`
- `POST /api/v1/patients/{id}/econsent/{id}/sign`
- `GET/POST /api/v1/visits`
- `GET /api/v1/visits/upcoming`

### SAE、药品、经费

- `GET/POST /api/v1/adverse-events`
- `GET/PUT /api/v1/adverse-events/{id}`
- `GET /api/v1/adverse-events/statistics`
- `GET/POST /api/v1/drugs/batches`
- `POST /api/v1/drugs/dispense`
- `POST /api/v1/drugs/return`
- `GET /api/v1/drugs/logs`
- `GET /api/v1/drugs/inventory-summary`
- `GET/POST /api/v1/contracts/contracts`
- `GET/POST /api/v1/contracts/payments`
- `GET /api/v1/contracts/budget-summary`

### 文档、监查、报表、通知

- `GET/POST /api/v1/documents`
- `POST /api/v1/documents/{id}/sign`
- `GET/POST /api/v1/monitoring/reports`
- `DELETE /api/v1/monitoring/reports/{id}`
- `GET/POST/PUT /api/v1/monitoring/issues`
- `GET /api/v1/reports/dashboard`
- `GET /api/v1/reports/enrollment-trend`
- `GET /api/v1/reports/site-enrollment`
- `GET /api/v1/reports/ae-summary`
- `GET /api/v1/reports/audit-logs`
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{id}/read`
- `POST /api/v1/notifications/read-all`

### IWRS

- `GET/POST/PATCH /api/v1/iwrs/schemes`
- `POST /api/v1/iwrs/schemes/{id}/activate`
- `GET /api/v1/iwrs/schemes/{id}/stats`
- `POST /api/v1/iwrs/assign`
- `GET /api/v1/iwrs/subjects`
- `POST /api/v1/iwrs/subjects/{id}/unblind`

> 最完整、最准确的接口定义请以 Swagger 为准：`/api/v1/docs`

---

## 前端说明

当前前端已经内置后端 API 客户端，并非单纯 mock 页面。

`assets/js/api-client.js` 的默认寻址规则为：

- 当前端运行在 `8899` 端口时，默认访问 `http://127.0.0.1:8898/api/v1`
- 其他 HTTP 场景默认走同源 `/api/v1`
- 若本地配置了 `localStorage.ctms_api_base`，优先使用该值

当前前端导航已覆盖：

- 工作台
- 试验管理
- IWRS
- 患者管理
- 药品管理
- 经费管理
- 统计报表
- 中心管理
- 人员管理
- 工时管理
- 设置

说明：

- 后端已有监查/通知/文档能力
- 但前端并非所有模块都完全开放在主导航上，实际可见入口请以页面实现为准

---

## 数据库说明

### 主初始化脚本

- 入口：`database/init/01_schema.sql`

当前脚本已覆盖核心 CTMS 表，包括：

- 用户、角色、组织、中心
- 试验、中心试验、里程碑
- 患者、eConsent、访视
- SAE/AE
- 药品批次、发放、回收
- 合同、付款
- 监查报告、质控问题
- 文档、通知、审计日志
- IWRS 方案、随机码、受试者随机化
- 工时

### 额外 SQL

仓库中还存在：

- `create_trial_extensions.sql`

该脚本用于补充 `trial_extensions` 相关结构，不属于 `01_schema.sql` 自动初始化的一部分；如果业务依赖该表，需要手动执行。

---

## 配置说明

### 当前主要环境变量

- 应用：`APP_ENV`、`DEBUG`、`SECRET_KEY`、`API_V1_STR`
- 数据库：`POSTGRES_*`、`DATABASE_URL`
- Redis：`REDIS_*`、`REDIS_URL`
- 文件存储：`S3_ENDPOINT_URL`、`S3_ACCESS_KEY`、`S3_SECRET_KEY`、`S3_BUCKET_NAME`
- 邮件：`SMTP_*`、`EMAILS_FROM_*`
- JWT：`ACCESS_TOKEN_EXPIRE_MINUTES`、`REFRESH_TOKEN_EXPIRE_DAYS`
- Celery：`CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`
- IWRS 外部同步：`IWRS_SAVE_PROJECT_ALL_URL`、`IWRS_SAVE_PROJECT_HOSPITAL_URL`

### 当前仓库状态说明

- `backend/.env.example` 与 `backend/app/core/config.py` 中的默认值并不完全一致
- 当前代码内仍存在开发/演示用默认敏感值，例如：
  - `SECRET_KEY`
  - 默认数据库密码
  - 默认超管密码
  - SMTP 账户信息

这些值只能用于开发或演示环境，生产环境务必改成安全值。

---

## 合规与安全实现

| 方向 | 当前实现 |
|------|----------|
| 认证 | JWT Access/Refresh、Bearer Token |
| 账号安全 | 登录失败锁定、密码强度校验 |
| 审计 | 认证与业务操作审计日志中间件 |
| 权限 | RBAC 权限依赖 |
| 反向代理 | Nginx 同源代理 `/api/` |
| 对象存储 | MinIO / S3 兼容 |

说明：

- README 中的“FDA 21 CFR Part 11 / GDPR / HIPAA / ISO 27001”应理解为项目设计目标与当前实现方向
- 是否满足正式审计或法规认证，仍需结合生产部署、运维控制、审计策略和安全评估进一步验证

---

## 已知限制

- `celery_worker` 当前为占位容器，异步任务未正式启用
- 文档模块当前以文档记录/签署为主，完整文件上传链路未在当前路由中完整暴露
- 当前 CORS 在 `main.py` 中使用 `allow_origin_regex=".*"`，与配置文件中的精细白名单并未完全一致
- 仓库内存在部分开发测试口径与生产口径混用的默认配置，部署前需清理

---

## 常用命令

### 查看后端日志

```bash
docker compose logs -f backend
```

### 查看服务状态

```bash
docker compose ps
```

### 进入后端容器

```bash
docker compose exec backend sh
```

### 打开 Swagger

```text
http://localhost:8898/api/v1/docs
```

### 健康检查

```bash
curl http://localhost:8898/health
```
