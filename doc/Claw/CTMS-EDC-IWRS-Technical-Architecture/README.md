# CTMS+EDC+IWRS 一体化临床试验平台 - 技术架构设计

**版本**: 1.0  
**创建日期**: 2026-05-27  
**状态**: 草案

---

## 📚 文档导航

本目录包含 CTMS+EDC+IWRS 平台的完整技术架构设计文档，为开发团队提供从架构设计到环境搭建的全面指导。

### 核心文档

1. **[微服务架构设计](./1-microservices-architecture.md)**
   - 12 个微服务详细设计
   - 服务通信机制
   - 多租户设计
   - 安全与性能设计

2. **[数据库 Schema 设计](./2-database-schema.md)**
   - PostgreSQL 表结构
   - ER 关系图
   - 索引优化策略
   - 数据归档方案

3. **[API 接口规范](./3-api-specifications.md)**
   - RESTful API 设计
   - 统一响应格式
   - OpenAPI 规范示例
   - 认证与授权

4. **[技术栈与开发环境](./4-technology-stack-setup.md)**
   - 技术选型详解
   - Docker Compose 配置
   - CI/CD 流水线
   - 监控与日志

---

## 🏗️ 架构概览

### 系统特点

- **12 个微服务**: 认证、CTMS、EDC、IWRS、病历夹、文档、报表、通知、安全、集成、配置、验证
- **多租户架构**: 基于 PostgreSQL RLS 实现数据隔离
- **CDISC 标准**: 底层数据模型符合 CDASH/SDTM 规范
- **安全合规**: 符合 21 CFR Part 11、GDPR、HIPAA 等法规
- **现代化技术栈**: React + TypeScript + Node.js + PostgreSQL

### 技术栈

```
前端：React 18 + Vite 5 + Ant Design 5 + Zustand
后端：Node.js 20 + Express + TypeScript + Prisma
数据库：PostgreSQL 15 + Redis 7
存储：MinIO (S3 兼容)
消息：RabbitMQ
部署：Docker + Kubernetes
监控：Prometheus + Grafana + ELK
```

---

## 📋 微服务清单

| 服务 | 端口 | 职责 |
|------|------|------|
| Auth Service | 3001 | 用户认证、SSO、RBAC 权限 |
| CTMS Service | 3002 | 试验管理、中心管理、工时管理 |
| EDC Service | 3003 | eCRF 设计、数据采集、核查规则 |
| IWRS Service | 3004 | 随机化算法、药物供应、破盲管理 |
| Portfolio Service | 3005 | 个人患者管理、表单设计 |
| Document Service | 3006 | eTMF 文档管理、版本控制 |
| Reporting Service | 3007 | 数据报表、仪表盘 |
| Notification Service | 3008 | 邮件、短信、WebSocket 推送 |
| Security Service | 3009 | 审计追踪、加密、合规报告 |
| Integration Service | 3010 | HL7/FHIR接口、API 网关 |
| Config Service | 3011 | 系统参数、租户配置 |
| Validation Service | 3012 | 数据验证、SDTM 映射 |

---

## 🚀 快速开始

### 前置要求

```bash
# 安装必要软件
- Git >= 2.30
- Node.js >= 20.x
- Docker >= 20.10
- Docker Compose >= 2.0
```

### 启动开发环境

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ctms-edc-iwrs.git
cd ctms-edc-iwrs

# 2. 启动基础设施
docker-compose up -d postgres redis minio rabbitmq

# 3. 运行数据库迁移
cd services/auth
npx prisma migrate dev
npx prisma generate

# 4. 启动后端服务
npm run dev:all

# 5. 启动前端应用
cd apps/web
npm run dev

# 6. 访问应用
# 前端：http://localhost:3000
# API 网关：http://localhost:8080
```

---

## 📊 数据库设计

### 核心实体关系

```
租户 (Tenants)
  ├─ 用户 (Users)
  │   └─ 角色 (Roles)
  │
  └─ 试验 (Studies)
      ├─ 研究中心 (Sites)
      ├─ eCRF 模板 (EDC Templates)
      ├─ 随机化配置 (IWRS Config)
      ├─ 工时记录 (Timesheets)
      └─ 审计日志 (Audit Logs)
```

### 多租户隔离

所有业务表包含 `tenant_id` 字段，使用 PostgreSQL **Row-Level Security** 实现数据隔离：

```sql
ALTER TABLE studies ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON studies
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

---

## 🔒 安全设计

### 认证与授权

- **JWT**: 服务间认证，1 小时过期
- **OAuth2**: 第三方登录（企业微信、钉钉）
- **RBAC**: 角色权限控制
- **CASBC**: 细粒度权限（基于属性）

### 数据加密

- **传输加密**: TLS 1.3
- **存储加密**: AES-256 / 国密 SM4
- **密码加密**: bcrypt (cost=12)

### 审计追踪

符合 21 CFR Part 11 要求：

- 所有关键操作记录审计日志
- 审计日志不可篡改（只读）
- 记录操作人、时间、IP、原因

---

## 📈 性能优化

### 缓存策略

- **Redis**: 热点数据（随机化配置、用户会话）
- **CDN**: 静态资源
- **HTTP 缓存**: ETag、Cache-Control

### 数据库优化

- **索引**: 为 `tenant_id`、`study_id` 创建复合索引
- **分区**: 审计日志按月分区
- **读写分离**: 主库写、从库读

### API 优化

- **分页**: 所有列表接口支持分页
- **字段选择**: 支持 `?fields=` 参数减少传输量
- **限流**: 每 IP 15 分钟 100 次请求

---

## 🛠️ 开发规范

### Git Commit 规范

```bash
feat(edc): 添加 eCRF 表单设计器
fix(auth): 修复 JWT 刷新令牌过期问题
docs(api): 更新 API 文档
refactor(ctms): 优化工时计算逻辑
test(iwrs): 添加随机化算法单元测试
```

### 代码审查清单

- [ ] TypeScript 严格模式
- [ ] API 输入验证（Zod）
- [ ] 错误处理完善
- [ ] 数据库查询优化
- [ ] 敏感数据加密
- [ ] 审计日志记录
- [ ] 单元测试覆盖
- [ ] API 文档更新

---

## 📝 文档维护

本文档由架构团队维护，如有问题或建议，请：

1. 提交 Issue
2. 发起 Pull Request
3. 联系架构团队

---

## 🔗 相关资源

- [PRD v2.0](../CTMS_EDC_IWRS_Platform_PRD_v2.md) - 产品需求文档
- [原型设计](../CTMS-EDC-IWRS-Prototype/) - 高保真原型
- [CDISC 标准](https://www.cdisc.org/) - 临床试验数据标准
- [21 CFR Part 11](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/electronic-signatures-electronic-records-guidance-compliance) - FDA 电子签名规范

---

## 📄 许可证

本项目采用专有软件许可证，详见 `LICENSE` 文件。

---

**最后更新**: 2026-05-27  
**维护团队**: 架构团队
