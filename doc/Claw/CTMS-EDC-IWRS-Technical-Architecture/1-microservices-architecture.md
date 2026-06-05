# CTMS+EDC+IWRS 平台 - 微服务架构设计

**文档版本**: 1.0  
**创建日期**: 2026-05-27  
**作者**: 架构团队  
**状态**: 草案

---

## 1. 架构概述

### 1.1 架构原则

本系统采用**微服务架构**，遵循以下核心原则：

- **单一职责**：每个服务专注于一个业务领域
- **松耦合**：服务间通过 API 通信，可独立部署
- **多租户隔离**：通过 `tenant_id` 实现数据隔离
- **标准优先**：数据模型符合 CDISC/SDTM 标准
- **安全合规**：符合 21 CFR Part 11、GDPR、HIPAA 等法规

### 1.2 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端层 (React + Vite)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 仪表盘   │ │  CTMS   │ │   EDC   │ │   IWRS   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API 网关层 (Nginx + Kong)                   │
│         路由转发 | 限流 | 认证 | 日志 | 监控                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    微服务层 (Node.js + TypeScript)            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │认证服务  │ │CTMS 服务  │ │EDC 服务   │ │IWRS 服务  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │病历夹服务│ │文档服务  │ │报表服务  │ │通知服务  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │安全服务  │ │集成服务  │ │配置服务  │ │验证服务  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据层                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │PostgreSQL│ │  Redis   │ │ MinIO    │ │ Elasticsearch│   │
│  │(主数据库) │ │ (缓存)   │ │(文件存储)│ │  (搜索)     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 微服务清单（12 个）

### 2.1 认证服务 (Auth Service)

**服务名**: `auth-service`  
**端口**: 3001  
**职责**: 用户认证、SSO、RBAC 权限管理

**核心功能**:
- JWT 令牌发放与刷新
- OAuth2 第三方登录（企业微信、钉钉）
- RBAC 权限控制（角色 - 权限 - 资源）
- CASBC 细粒度权限（基于属性的访问控制）
- 会话管理（登录日志、并发控制）

**API 端点示例**:
```
POST   /api/v1/auth/login          # 用户登录
POST   /api/v1/auth/logout         # 用户登出
POST   /api/v1/auth/refresh        # 刷新令牌
GET    /api/v1/auth/profile        # 获取用户信息
GET    /api/v1/auth/permissions    # 获取用户权限
POST   /api/v1/auth/sso/wechat     # 企业微信 SSO
```

**技术栈**:
- JWT (jsonwebtoken)
- OAuth2 (passport)
- bcrypt (密码加密)
- Redis (会话缓存)

---

### 2.2 CTMS 服务 (CTMS Service)

**服务名**: `ctms-service`  
**端口**: 3002  
**职责**: 试验管理、中心管理、工时管理、收支管理、审批工作流

**核心功能**:
- 试验项目全生命周期管理
- 研究中心管理与状态跟踪
- 工时填报与审批流程
- 项目收支与成本核算
- 审批工作流引擎（多级审批）

**API 端点示例**:
```
# 试验管理
GET    /api/v1/studies             # 列出试验
POST   /api/v1/studies             # 创建试验
GET    /api/v1/studies/:id         # 获取试验详情
PUT    /api/v1/studies/:id         # 更新试验
DELETE /api/v1/studies/:id         # 删除试验

# 中心管理
GET    /api/v1/studies/:id/sites   # 列出研究中心
POST   /api/v1/studies/:id/sites   # 添加中心

# 工时管理
GET    /api/v1/timesheets          # 列出工时记录
POST   /api/v1/timesheets          # 提交工时
POST   /api/v1/timesheets/:id/approve  # 审批工时

# 审批工作流
POST   /api/v1/approvals           # 提交审批
GET    /api/v1/approvals/pending   # 待审批列表
```

**技术栈**:
- 工作流引擎 (workflow.js)
- 状态机 (xstate)
- PostgreSQL (业务数据)

---

### 2.3 EDC 服务 (EDC Service)

**服务名**: `edc-service`  
**端口**: 3003  
**职责**: eCRF 设计、数据采集、核查规则、质疑管理

**核心功能**:
- 拖拉拽式 eCRF 表单设计器
- CDASH 标准字段库
- 动态表单渲染引擎
- 数据核查规则引擎（Edit Check）
- 质疑（Query）发起与回复
- 数据修改审计追踪

**API 端点示例**:
```
# eCRF 设计
GET    /api/v1/ecrf/templates      # 列出模板
POST   /api/v1/ecrf/templates      # 创建模板
GET    /api/v1/ecrf/templates/:id  # 获取模板
PUT    /api/v1/ecrf/templates/:id  # 更新模板

# 数据录入
GET    /api/v1/ecrf/forms/:studyId # 列出表单
POST   /api/v1/ecrf/data           # 提交数据
GET    /api/v1/ecrf/data/:id       # 获取数据

# 核查规则
POST   /api/v1/ecrf/edit-checks    # 创建核查规则
GET    /api/v1/ecrf/edit-checks    # 列出规则

# 质疑管理
POST   /api/v1/ecrf/queries        # 发起质疑
POST   /api/v1/ecrf/queries/:id/reply  # 回复质疑
```

**技术栈**:
- 动态表单引擎 (react-jsonschema-form)
- 规则引擎 (json-rules-engine)
- PostgreSQL (表单数据)
- MinIO (eCRF 附件存储)

---

### 2.4 IWRS 服务 (IWRS Service)

**服务名**: `iwrs-service`  
**端口**: 3004  
**职责**: 随机化算法、药物供应管理、破盲管理

**核心功能**:
- 随机化算法引擎（简单/区组/分层/动态）
- 患者随机化与重新随机化
- 药物库存管理（入库/出库/盘点/调拨）
- 紧急破盲管理
- 随机化报告与平衡性分析

**API 端点示例**:
```
# 随机化配置
POST   /api/v1/iwrs/config         # 配置随机化方案
GET    /api/v1/iwrs/config/:studyId # 获取配置

# 患者随机化
POST   /api/v1/iwrs/randomize      # 执行随机化
POST   /api/v1/iwrs/re-randomize   # 重新随机化
GET    /api/v1/iwrs/:subjectId     # 查询随机化状态

# 破盲管理
POST   /api/v1/iwrs/unblind        # 紧急破盲申请
POST   /api/v1/iwrs/unblind/:id/approve  # 破盲审批

# 药物供应
GET    /api/v1/iwrs/inventory      # 库存查询
POST   /api/v1/iwrs/inventory/in   # 药物入库
POST   /api/v1/iwrs/inventory/out  # 药物出库
```

**技术栈**:
- 随机化引擎 (自研)
- 库存算法 (自研)
- PostgreSQL (随机化记录)
- Redis (随机化缓存，<200ms 响应)

---

### 2.5 病历夹服务 (Doctor Portfolio Service)

**服务名**: `portfolio-service`  
**端口**: 3005  
**职责**: 个人患者管理、表单设计、数据录入、CDISC 映射

**核心功能**:
- 患者档案管理（基本信息、诊断、治疗历史）
- 随访计划与提醒
- 自定义表单设计器（复用 EDC 引擎）
- 随访数据录入
- SDTM 数据映射与导出

**API 端点示例**:
```
# 患者管理
GET    /api/v1/portfolio/patients  # 列出患者
POST   /api/v1/portfolio/patients  # 创建患者档案
GET    /api/v1/portfolio/patients/:id  # 获取患者详情

# 随访管理
POST   /api/v1/portfolio/followups # 创建随访计划
GET    /api/v1/portfolio/followups/upcoming  # 待随访列表

# 表单设计
POST   /api/v1/portfolio/forms     # 创建随访表单
GET    /api/v1/portfolio/forms     # 列出表单

# 数据导出
POST   /api/v1/portfolio/export/sdtml  # 导出 SDTM 格式
```

**技术栈**:
- 表单引擎 (复用 EDC)
- CDISC 映射 (自研)
- PostgreSQL (患者数据)

---

### 2.6 文档服务 (Document Service)

**服务名**: `document-service`  
**端口**: 3006  
**职责**: eTMF 文档管理、在线编辑、版本控制

**核心功能**:
- eTMF 文档树管理
- 文件上传与存储（WebDAV）
- 在线文档编辑（Collabora/OnlyOffice 集成）
- 版本控制与历史追溯
- 文档权限控制
- 电子签名集成

**API 端点示例**:
```
# 文档管理
GET    /api/v1/documents/tree      # 获取文档树
POST   /api/v1/documents           # 上传文档
GET    /api/v1/documents/:id       # 获取文档详情
DELETE /api/v1/documents/:id       # 删除文档

# 版本控制
GET    /api/v1/documents/:id/versions  # 版本历史
POST   /api/v1/documents/:id/versions  # 创建新版本

# 在线编辑
GET    /api/v1/documents/:id/edit  # 获取编辑链接
POST   /api/v1/documents/:id/save  # 保存编辑
```

**技术栈**:
- WebDAV (webdav-client)
- Collabora/OnlyOffice (在线编辑)
- MinIO (文件存储)
- PostgreSQL (元数据)

---

### 2.7 报表服务 (Reporting Service)

**服务名**: `reporting-service`  
**端口**: 3007  
**职责**: 数据报表、仪表盘、自定义查询

**核心功能**:
- 预定义报表模板（入组进度、数据质量、工时统计）
- 自定义查询构建器
- 数据可视化（图表、仪表盘）
- 报表导出（PDF、Excel）
- 定时报表生成与推送

**API 端点示例**:
```
# 预定义报表
GET    /api/v1/reports/enrollment  # 入组进度报表
GET    /api/v1/reports/data-quality  # 数据质量报表
GET    /api/v1/reports/timesheet   # 工时统计报表

# 自定义查询
POST   /api/v1/reports/query       # 执行自定义查询

# 报表导出
POST   /api/v1/reports/:id/export/pdf  # 导出 PDF
POST   /api/v1/reports/:id/export/excel  # 导出 Excel

# 定时报表
POST   /api/v1/reports/schedules   # 创建定时报表
```

**技术栈**:
- Superset/Metabase (可视化)
- OLAP (立方体分析)
- PDF 生成 (pdfkit)
- Excel 导出 (xlsx)

---

### 2.8 通知服务 (Notification Service)

**服务名**: `notification-service`  
**端口**: 3008  
**职责**: 邮件、短信、站内信、WebSocket 推送

**核心功能**:
- 多渠道通知（邮件、短信、站内信、WebSocket）
- 通知模板管理
- 批量通知发送
- 通知历史记录
- WebSocket 实时推送

**API 端点示例**:
```
# 发送通知
POST   /api/v1/notifications/email # 发送邮件
POST   /api/v1/notifications/sms   # 发送短信
POST   /api/v1/notifications/inapp # 站内信

# 通知模板
GET    /api/v1/notifications/templates  # 列出模板
POST   /api/v1/notifications/templates  # 创建模板

# WebSocket
WS     /ws/notifications           # WebSocket 实时推送
```

**技术栈**:
- RabbitMQ (消息队列)
- WebSocket (ws)
- 邮件服务 (nodemailer)
- 短信服务 (第三方 API)

---

### 2.9 安全服务 (Security Service) 【新增】

**服务名**: `security-service`  
**端口**: 3009  
**职责**: 审计追踪、加密、脱敏、合规报告

**核心功能**:
- 审计追踪（不可篡改，只读）
- 数据加密（AES-256、国密 SM4）
- 数据脱敏（PII 保护）
- 合规性审计报告
- 电子签名管理（21 CFR Part 11）

**API 端点示例**:
```
# 审计追踪
GET    /api/v1/security/audit/logs # 查询审计日志
GET    /api/v1/security/audit/:entityType/:id  # 实体审计历史

# 数据加密
POST   /api/v1/security/encrypt    # 加密数据
POST   /api/v1/security/decrypt    # 解密数据

# 数据脱敏
POST   /api/v1/security/mask       # 数据脱敏

# 合规报告
POST   /api/v1/security/compliance/reports  # 生成合规报告
```

**技术栈**:
- AES-256 (crypto)
- 国密 SM4 (sm-crypto)
- PostgreSQL (审计日志，只读)

---

### 2.10 集成服务 (Integration Service) 【新增】

**服务名**: `integration-service`  
**端口**: 3010  
**职责**: HL7/FHIR接口、API 网关、消息队列、第三方系统对接

**核心功能**:
- HL7 v2/v3接口
- FHIR R4 标准支持
- API 网关管理
- 消息队列（Kafka/RabbitMQ）
- 第三方系统对接（EHR、LIS、PACS）

**API 端点示例**:
```
# HL7/FHIR接口
POST   /api/v1/integration/hl7     # 发送 HL7 消息
GET    /api/v1/integration/fhir/:resource  # FHIR 资源查询
POST   /api/v1/integration/fhir/:resource  # FHIR 资源创建

# API 管理
GET    /api/v1/integration/apis    # 列出 API
POST   /api/v1/integration/apis    # 创建 API 对接

# 消息队列
POST   /api/v1/integration/mq/publish  # 发布消息
```

**技术栈**:
- HL7 (hl7.js)
- FHIR (fhirclient)
- Kafka/RabbitMQ (消息队列)

---

### 2.11 配置服务 (Configuration Service) 【新增】

**服务名**: `config-service`  
**端口**: 3011  
**职责**: 系统参数、租户配置、特性开关

**核心功能**:
- 系统参数配置
- 多租户配置管理
- 特性开关（Feature Flags）
- 配置版本管理
- 配置动态刷新

**API 端点示例**:
```
# 系统配置
GET    /api/v1/config/system       # 获取系统配置
PUT    /api/v1/config/system       # 更新系统配置

# 租户配置
GET    /api/v1/config/tenants/:id  # 获取租户配置
PUT    /api/v1/config/tenants/:id  # 更新租户配置

# 特性开关
GET    /api/v1/config/features     # 列出特性开关
PUT    /api/v1/config/features/:id # 开关控制
```

**技术栈**:
- 配置中心 (nacos/apollo)
- Redis (配置缓存)

---

### 2.12 验证服务 (Validation Service) 【新增】

**服务名**: `validation-service`  
**端口**: 3012  
**职责**: 数据验证、SDTM 映射、质量检查

**核心功能**:
- 数据合理性检查
- 数据范围检查
- SDTM 映射配置
- DVS 验证工具集成
- 数据质量报告

**API 端点示例**:
```
# 数据验证
POST   /api/v1/validation/check    # 执行数据验证
GET    /api/v1/validation/results  # 查询验证结果

# SDTM 映射
POST   /api/v1/validation/sdtml/mapping  # 创建映射
GET    /api/v1/validation/sdtml/mapping/:id  # 获取映射
POST   /api/v1/validation/sdtml/export  # 导出 SDTM 数据

# DVS 验证
POST   /api/v1/validation/dvs      # 执行 DVS 验证
GET    /api/v1/validation/dvs/results  # DVS 报告
```

**技术栈**:
- DVS (Data Validation System)
- 规则引擎 (json-rules-engine)
- CDISC 标准库

---

## 3. 服务通信机制

### 3.1 同步通信 (REST API)

适用于实时性要求高的场景：

```typescript
// 使用 Axios 进行 HTTP 调用
const axios = require('axios');

// CTMS 服务调用 EDC 服务
async function getStudyForms(studyId: string) {
  const response = await axios.get('http://edc-service:3003/api/v1/ecrf/forms/:studyId', {
    headers: { 'X-Request-ID': generateRequestId() }
  });
  return response.data;
}
```

### 3.2 异步通信 (消息队列)

适用于批量处理、解耦场景：

```typescript
// 使用 RabbitMQ
const amqp = require('amqplib');

// 发送消息
async function sendNotification(message: any) {
  const channel = await conn.createChannel();
  channel.assertQueue('notifications');
  channel.sendToQueue('notifications', Buffer.from(JSON.stringify(message)));
}
```

### 3.3 服务发现

使用 **Consul** 或 **Etcd** 进行服务注册与发现：

```yaml
# Consul 配置
services:
  - name: auth-service
    port: 3001
    checks:
      - http: http://localhost:3001/health
        interval: 10s
```

---

## 4. 多租户设计

### 4.1 租户隔离策略

所有业务表增加 `tenant_id` 字段，使用 PostgreSQL **Row-Level Security (RLS)** 实现数据隔离：

```sql
-- 启用 RLS
ALTER TABLE edc_templates ENABLE ROW LEVEL SECURITY;

-- 创建租户隔离策略
CREATE POLICY tenant_isolation_policy ON edc_templates
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

### 4.2 租户上下文传递

通过 HTTP Header 传递租户 ID：

```typescript
// 中间件：设置租户上下文
app.use((req, res, next) => {
  const tenantId = req.headers['x-tenant-id'];
  db.query(`SET app.current_tenant TO '${tenantId}'`);
  next();
});
```

---

## 5. 安全设计

### 5.1 认证与授权

- **JWT**: 服务间认证
- **OAuth2**: 第三方集成
- **RBAC**: 角色权限控制
- **CASBC**: 细粒度权限

### 5.2 数据加密

- **传输加密**: TLS 1.3
- **存储加密**: AES-256 / 国密 SM4
- **密码加密**: bcrypt (cost=12)

### 5.3 审计追踪

符合 21 CFR Part 11 要求：

```typescript
interface AuditLog {
  id: UUID;
  tenant_id: UUID;
  entity_type: string;     // 实体类型（如：Study、Patient）
  entity_id: UUID;         // 实体 ID
  action: string;          // 操作（CREATE、UPDATE、DELETE）
  old_value?: any;         // 旧值
  new_value?: any;         // 新值
  user_id: UUID;           // 操作人
  timestamp: DateTime;     // 操作时间
  ip_address: string;      // IP 地址
  reason?: string;         // 操作原因
}
```

---

## 6. 性能设计

### 6.1 缓存策略

- **Redis**: 热点数据缓存（随机化配置、用户会话）
- **CDN**: 静态资源缓存
- **HTTP 缓存**: 响应缓存（ETag、Cache-Control）

### 6.2 数据库优化

- **索引**: 为 `tenant_id`、`study_id`、`created_at` 创建复合索引
- **分区**: 按 `tenant_id` 或 `created_at` 分区
- **读写分离**: 主库写、从库读

### 6.3 负载均衡

- **Nginx**: 反向代理与负载均衡
- **Kong**: API 网关与限流

---

## 7. 监控与日志

### 7.1 应用监控

- **Prometheus**: 指标采集
- **Grafana**: 可视化仪表盘
- **AlertManager**: 告警通知

### 7.2 日志管理

- **ELK Stack**: Elasticsearch + Logstash + Kibana
- **结构化日志**: JSON 格式
- **日志分级**: ERROR、WARN、INFO、DEBUG

### 7.3 分布式追踪

- **Jaeger**: 分布式追踪
- **Trace ID**: 跨服务追踪请求

---

## 8. 部署架构

### 8.1 Docker Compose (开发环境)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ctms_edc
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  auth-service:
    build: ./services/auth
    ports:
      - "3001:3001"
    depends_on:
      - postgres
      - redis

  # ...其他服务
```

### 8.2 Kubernetes (生产环境)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: myregistry/auth-service:latest
        ports:
        - containerPort: 3001
```

---

## 9. 技术栈总结

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **前端** | React + Vite + Ant Design | 响应式 UI 框架 |
| **后端** | Node.js + TypeScript + Express | 微服务框架 |
| **数据库** | PostgreSQL 15 | 主数据库 |
| **缓存** | Redis 7 | 缓存与会话 |
| **文件存储** | MinIO | 对象存储（S3 兼容） |
| **消息队列** | RabbitMQ / Kafka | 异步通信 |
| **API 网关** | Kong / Nginx | 路由、限流、认证 |
| **搜索** | Elasticsearch | 全文搜索 |
| **监控** | Prometheus + Grafana | 指标监控 |
| **日志** | ELK Stack | 日志管理 |
| **部署** | Docker + Kubernetes | 容器编排 |
| **CI/CD** | GitHub Actions | 自动化部署 |

---

## 10. 下一步

1. **数据库 Schema 设计**：详细设计每个服务的数据库表结构
2. **API 接口规范**：定义 RESTful API 契约
3. **开发环境搭建**：配置 Docker Compose 和脚手架
4. **核心服务开发**：优先开发认证服务、CTMS 服务、EDC 服务

---

**文档结束**
