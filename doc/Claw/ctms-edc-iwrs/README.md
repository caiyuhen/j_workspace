# CTMS+EDC+IWRS 平台

临床试验管理系统 (CTMS) + 电子数据采集系统 (EDC) + 交互式随机化与药物供应管理系统 (IWRS) 一体化平台。

## 🎯 项目概述

这是一个符合 **21 CFR Part 11** 和 **CDISC 标准** 的临床试验管理 SaaS 平台，支持多租户架构，适用于制药企业、CRO、临床研究中心等。

### 核心功能模块

1. **CTMS（临床试验管理）**
   - 试验项目管理
   - 研究中心管理
   - 工时记录与审批
   - 预算管理
   - 流程审批

2. **EDC（电子数据采集）**
   - eCRF 可视化设计器（CDASH 标准）
   - 数据录入与验证
   - 质疑管理
   - 数据审核
   - SDTM 数据导出

3. **IWRS（随机化与药物供应）**
   - 动态随机化算法
   - 分层区组设计
   - 药物库存管理
   - 破盲管理
   - 受试者入组

4. **eTMF（电子试验主文件）**
   - 文档版本控制
   - 审计轨迹
   - 电子签名
   - 文档审批流程

5. **医生病历夹**
   - 患者档案管理
   - 随访数据收集
   - 检验报告管理
   - 时间线视图

6. **报告中心**
   - 试验进度仪表板
   - 数据质量报告
   - 入组进度分析
   - 自定义报表

## 🏗️ 技术架构

### 微服务架构（12 个服务）

```
auth-service          # 认证与授权 (3001)
ctms-service          # 临床试验管理 (3002)
edc-service           # 电子数据采集 (3003)
iwrs-service          # 随机化与药物供应 (3004)
portfolio-service     # 医生病历夹 (3005)
document-service      # eTMF 文档管理 (3006)
reporting-service     # 报表生成 (3007)
notification-service  # 通知服务 (3008)
security-service      # 安全审计 (3009)
integration-service   # 系统集成 (3010)
config-service        # 系统配置 (3011)
validation-service    # 数据验证 (3012)
```

### 技术栈

- **前端**: React 18 + Vite 5 + Ant Design 5 + Zustand 4
- **后端**: Node.js 20 + Express 4 + TypeScript + Prisma 5
- **数据库**: PostgreSQL 15（多租户 RLS）
- **缓存**: Redis 7
- **消息队列**: RabbitMQ 3
- **对象存储**: MinIO
- **API 网关**: Nginx
- **监控**: Prometheus + Grafana
- **日志**: Elasticsearch + Kibana

## 📋 前置要求

- ✅ Git ≥ 2.30
- ✅ Node.js ≥ 20.x
- ✅ Docker ≥ 20.10
- ✅ Docker Compose ≥ 2.0

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd ctms-edc-iwrs
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，根据实际情况修改配置
```

### 3. 启动开发环境

```bash
# 启动所有服务（基础设施 + 微服务 + 前端）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止所有服务
docker-compose down
```

### 4. 访问系统

- **前端应用**: http://localhost:5173
- **API 网关**: http://localhost:80
- **Nginx 状态页**: http://localhost:80/nginx_status
- **MinIO 控制台**: http://localhost:9001
- **RabbitMQ 管理**: http://localhost:15672 (guest/guest)
- **Kibana**: http://localhost:5601
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 📁 项目结构

```
ctms-edc-iwrs/
├── services/
│   ├── auth-service/          # 认证服务
│   ├── ctms-service/          # CTMS 服务
│   ├── edc-service/           # EDC 服务
│   ├── iwrs-service/          # IWRS 服务
│   ├── portfolio-service/     # 医生病历夹
│   ├── document-service/      # eTMF 文档
│   ├── reporting-service/     # 报表服务
│   ├── notification-service/  # 通知服务
│   ├── security-service/      # 安全服务
│   ├── integration-service/   # 集成服务
│   ├── config-service/        # 配置服务
│   └── validation-service/    # 验证服务
├── frontend/                  # React 前端
├── infrastructure/
│   ├── sql/                   # 数据库初始化脚本
│   ├── nginx/                 # Nginx 配置
│   ├── prometheus/            # Prometheus 配置
│   └── grafana/               # Grafana 配置
├── scripts/                   # 工具脚本
├── docs/                      # 文档
├── tests/                     # 测试
├── docker-compose.yml         # Docker Compose 配置
├── .env.example              # 环境变量模板
├── .gitignore                # Git 忽略规则
└── README.md                 # 项目说明
```

## 🎓 核心特性

### CDISC 标准支持

- ✅ CDASH 字段命名规范
- ✅ SDTM 数据结构
- ✅ eCRF 标准化设计
- ✅ ADaM 导出支持（计划中）

### 21 CFR Part 11 合规

- ✅ 审计追踪（不可篡改）
- ✅ 电子签名
- ✅ 数据加密（传输 + 存储）
- ✅ 访问控制（RBAC）
- ✅ 数据完整性保护

### 多租户架构

- ✅ 租户数据隔离（PostgreSQL RLS）
- ✅ 租户级配置
- ✅ 租户级用户管理
- ✅ 租户级审计日志

### 安全特性

- ✅ JWT 认证
- ✅ OAuth2 SSO（企业微信）
- ✅ 细粒度权限控制
- ✅ 审计日志（Elasticsearch）
- ✅ API 限流

## 📚 文档资源

- [PRD v2.0](../CTMS_EDC_IWRS_Platform_PRD_v2.md) - 产品需求文档
- [产品原型](../CTMS-EDC-IWRS-Prototype/) - 高保真原型
- [技术架构](../CTMS-EDC-IWRS-Technical-Architecture/) - 架构设计文档
- [API 规范](../CTMS-EDC-IWRS-Technical-Architecture/3-api-specifications.md) - API 接口文档
- [数据库设计](../CTMS-EDC-IWRS-Technical-Architecture/2-database-schema.md) - 数据库 Schema

## 🛠️ 开发指南

### 本地开发环境设置

```bash
# 安装依赖（在每个服务目录下）
cd services/auth-service
npm install

# 启动开发服务器
npm run dev

# 运行测试
npm test

# 类型检查
npm run type-check

# 代码格式化
npm run format
```

### 数据库迁移

```bash
# 创建新迁移
npx prisma migrate dev --name <migration_name>

# 运行迁移
npx prisma migrate deploy

# 重置数据库
npx prisma migrate reset
```

### 生成 Prisma Client

```bash
npx prisma generate
```

## 🧪 测试

```bash
# 单元测试
npm test

# 端到端测试
npm run test:e2e

# 覆盖率报告
npm run test:coverage
```

## 📊 监控与日志

### Prometheus 指标端点

每个微服务都暴露 `/metrics` 端点：

```
http://localhost:3001/metrics  # Auth Service
http://localhost:3002/metrics  # CTMS Service
...
```

### Grafana 仪表板

预配置了以下仪表板：

- 系统健康度
- API 性能
- 数据库性能
- 消息队列状态
- 错误率统计

## 🔒 安全最佳实践

1. **密码策略**
   - 最小长度：12 字符
   - 包含大写字母、小写字母、数字、特殊字符
   - 90 天强制更换

2. **API 安全**
   - 启用 CORS 白名单
   - 实施速率限制（1000 请求/分钟）
   - 所有 API 需要 JWT 认证

3. **数据安全**
   - 敏感字段 AES-256 加密
   - 传输层 TLS 1.3
   - 数据库连接 SSL

## 🤝 贡献指南

### Git Commit 规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例**:
```
feat(edc): 添加 eCRF 拖拽设计器

- 实现组件库
- 实现画布区域
- 实现属性配置
- 添加撤销/重做功能

Closes #123
```

### 代码审查清单

- [ ] 代码符合 TypeScript 严格模式
- [ ] 所有输入都有验证（Zod）
- [ ] 错误处理完整
- [ ] 单元测试覆盖
- [ ] 文档已更新
- [ ] 性能影响已评估

## 📝 许可证

本项目采用专有软件许可证。版权所有 © 2024.

## 📞 联系方式

- 技术支持：support@ctms-platform.com
- 问题反馈：https://github.com/your-org/ctms-edc-iwrs/issues

## 🙏 致谢

感谢以下开源项目：

- [Ant Design](https://ant.design/) - 企业级 UI 组件库
- [Prisma](https://www.prisma.io/) - 下一代 ORM
- [Zustand](https://github.com/pmndrs/zustand) - 状态管理
- [MinIO](https://min.io/) - 对象存储

---

**当前版本**: 0.1.0-alpha
**构建时间**: 2026-05-27
**开发阶段**: 原型验证期
