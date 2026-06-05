# 项目结构说明

## 📁 完整目录树

```
ctms-edc-iwrs/
│
├── 📂 services/                     # 微服务目录
│   ├── 📂 auth-service/             # 认证与授权服务 (端口 3001)
│   │   ├── src/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── Dockerfile
│   ├── 📂 ctms-service/             # CTMS 临床试验管理 (端口 3002)
│   ├── 📂 edc-service/              # EDC 电子数据采集 (端口 3003)
│   ├── 📂 iwrs-service/             # IWRS 随机化药物供应 (端口 3004)
│   ├── 📂 portfolio-service/        # 医生病历夹 (端口 3005)
│   ├── 📂 document-service/         # eTMF 文档管理 (端口 3006)
│   ├── 📂 reporting-service/        # 报表生成 (端口 3007)
│   ├── 📂 notification-service/     # 通知服务 (端口 3008)
│   ├── 📂 security-service/         # 安全审计 (端口 3009)
│   ├── 📂 integration-service/      # 系统集成 (端口 3010)
│   ├── 📂 config-service/           # 系统配置 (端口 3011)
│   └── 📂 validation-service/       # 数据验证 (端口 3012)
│
├── 📂 frontend/                     # React 前端应用 (端口 5173)
│   ├── src/
│   │   ├── components/              # 公共组件
│   │   ├── pages/                   # 页面组件
│   │   ├── stores/                  # Zustand 状态管理
│   │   ├── services/                # API 服务
│   │   ├── utils/                   # 工具函数
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── 📂 infrastructure/               # 基础设施配置
│   ├── 📂 sql/                      # 数据库脚本
│   │   ├── init.sql                 # 初始化脚本
│   │   └── migrations/              # 数据库迁移
│   ├── 📂 nginx/                    # Nginx 配置
│   │   ├── nginx.conf
│   │   ├── conf.d/
│   │   └── ssl/
│   ├── 📂 prometheus/               # Prometheus 监控
│   │   └── prometheus.yml
│   └── 📂 grafana/                  # Grafana 仪表板
│       ├── dashboards/
│       └── datasources/
│
├── 📂 scripts/                      # 工具脚本
│   ├── check-prerequisites.sh       # Linux/Mac环境检查
│   ├── check-prerequisites.ps1      # Windows 环境检查
│   ├── setup-database.sh            # 数据库初始化
│   └── deploy.sh                    # 部署脚本
│
├── 📂 docs/                         # 文档
│   ├── api/                         # API 文档
│   ├── architecture/                # 架构文档
│   └── guides/                      # 使用指南
│
├── 📂 tests/                        # 测试
│   ├── e2e/                         # 端到端测试
│   ├── integration/                 # 集成测试
│   └── fixtures/                    # 测试数据
│
├── 📄 docker-compose.yml           # Docker Compose 主配置
├── 📄 .env.example                 # 环境变量模板
├── 📄 .gitignore                   # Git 忽略规则
├── 📄 README.md                    # 项目说明
└── 📄 LICENSE                      # 许可证

```

## 🎯 各目录职责说明

### services/ - 微服务层

包含 12 个独立的微服务，每个服务都是独立的 Node.js 项目:

**服务间通信**:
- 同步通信：REST API (Axios/Fetch)
- 异步通信：RabbitMQ 消息队列
- 服务发现：通过 Docker 网络名称解析

**统一结构** (每个服务):
```
service-name/
├── src/
│   ├── controllers/     # 路由控制器
│   ├── services/        # 业务逻辑
│   ├── models/          # 数据模型
│   ├── dto/             # 数据传输对象 (Zod)
│   ├── middleware/      # 中间件
│   ├── routes/          # 路由定义
│   └── index.ts         # 入口文件
├── prisma/
│   ├── schema.prisma    # Prisma Schema
│   └── migrations/      # 数据库迁移
├── tests/
├── package.json
└── Dockerfile
```

### frontend/ - 前端应用

**技术栈**:
- React 18 + TypeScript
- Vite 5 (构建工具)
- Ant Design 5 (UI 组件库)
- Zustand 4 (状态管理)
- React Router 6 (路由)
- Axios (HTTP 客户端)

**路由结构**:
```
/
├── /login                      # 登录页
├── /dashboard                  # 仪表盘
├── /ctms/
│   ├── /studies               # 试验列表
│   ├── /studies/:id           # 试验详情
│   ├── /sites                 # 中心管理
│   └── /timesheets            # 工时记录
├── /edc/
│   ├── /templates             # eCRF 模板
│   ├── /forms/:studyId        # 数据录入
│   └── /queries               # 质疑管理
├── /iwrs/
│   ├── /config                # 随机化配置
│   └── /enroll                # 受试者入组
├── /etmf/                      # 文档管理
├── /portfolio/                 # 医生病历夹
└── /reports/                   # 报表中心
```

### infrastructure/ - 基础设施

**SQL 脚本**:
- `init.sql`: 初始化数据库、租户、管理员账号
- `migrations/`: Prisma 迁移文件（按时间排序）

**Nginx 配置**:
- `nginx.conf`: 主配置
- `conf.d/`: 各微服务反向代理配置
- `ssl/`: SSL 证书（生产环境）

**监控配置**:
- Prometheus: 指标采集配置
- Grafana: 预置仪表板 JSON

### scripts/ - 自动化脚本

- `check-prerequisites.*`: 环境检查
- `setup-database.sh`: 数据库初始化
- `deploy.sh`: 一键部署（开发环境）
- `backup.sh`: 数据备份

### docs/ - 文档

- `api/`: OpenAPI 规范（YAML）
- `architecture/`: 架构决策记录（ADR）
- `guides/`: 开发指南、运维手册

### tests/ - 测试

- `e2e/`: Cypress/Playwright 端到端测试
- `integration/`: 服务间集成测试
- `fixtures/`: 测试数据（种子数据）

## 🔗 服务依赖关系

```
前端 (React)
    ↓ HTTP
Nginx (API 网关)
    ↓ 反向代理
┌──────────────────────────────────────┐
│  业务微服务层                          │
│  ├── Auth Service                    │
│  ├── CTMS Service ───→ RabbitMQ      │
│  ├── EDC Service ────→ RabbitMQ      │
│  ├── IWRS Service                    │
│  ├── Portfolio Service               │
│  ├── Document Service ──→ RabbitMQ   │
│  ├── Reporting Service ──→ RabbitMQ  │
│  ├── Notification Service ← RabbitMQ │
│  ├── Security Service ──→ RabbitMQ   │
│  ├── Integration Service             │
│  ├── Config Service                  │
│  └── Validation Service              │
└──────────────────────────────────────┘
    ↓ 数据访问
┌──────────────────────────────────────┐
│  数据层                               │
│  ├── PostgreSQL (主数据库)            │
│  ├── Redis (缓存)                     │
│  ├── MinIO (对象存储)                 │
│  └── Elasticsearch (日志/搜索)         │
└──────────────────────────────────────┘
```

## 📝 开发建议

### 1. 本地开发

```bash
# 启动单个微服务（开发模式）
cd services/auth-service
npm install
npm run dev

# 启动前端（开发模式）
cd frontend
npm install
npm run dev
```

### 2. 数据库操作

```bash
# 生成 Prisma Client
cd services/auth-service
npx prisma generate

# 启动 Prisma Studio（数据库 GUI）
npx prisma studio

# 创建迁移
npx prisma migrate dev --name add_new_field
```

### 3. 测试

```bash
# 单元测试
npm test

# 集成测试
npm run test:integration

# 端到端测试
npm run test:e2e
```

## 🎓 学习路径

**新手入门**:
1. 阅读 [README.md](../README.md) 了解项目概览
2. 查看 [PRD 文档](../CTMS_EDC_IWRS_Platform_PRD_v2.md) 理解业务
3. 浏览 [产品原型](../CTMS-EDC-IWRS-Prototype/) 熟悉界面
4. 阅读 [技术架构](../CTMS-EDC-IWRS-Technical-Architecture/) 文档

**开发准备**:
1. 运行环境检查脚本
2. 配置环境变量
3. 启动 Docker 环境
4. 阅读 API 规范文档

**开始开发**:
1. 选择要开发的服务
2. 理解服务职责和 API
3. 编写业务代码
4. 添加单元测试
5. 提交 PR 并等待审查

---

**最后更新**: 2026-05-27
**维护者**: CTMS+EDC+IWRS 开发团队
