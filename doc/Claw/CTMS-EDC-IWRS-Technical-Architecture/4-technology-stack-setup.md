# CTMS+EDC+IWRS 平台 - 技术栈与开发环境搭建

**文档版本**: 1.0  
**创建日期**: 2026-05-27  
**作者**: 架构团队  
**状态**: 草案

---

## 1. 技术栈总结

### 1.1 前端技术栈

| 类别 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **框架** | React | 18.x | UI 框架 |
| **构建工具** | Vite | 5.x | 快速开发和构建 |
| **语言** | TypeScript | 5.x | 类型安全 |
| **UI 组件库** | Ant Design | 5.x | 企业级 UI 组件 |
| **状态管理** | Zustand | 4.x | 轻量级状态管理 |
| **路由** | React Router | 6.x | 路由管理 |
| **HTTP 客户端** | Axios | 1.x | API 请求 |
| **表单** | React Hook Form | 7.x | 表单管理 |
| **验证** | Zod | 3.x | 数据验证 |
| **图表** | ECharts | 5.x | 数据可视化 |

### 1.2 后端技术栈

| 类别 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **运行时** | Node.js | 20.x | JavaScript 运行时 |
| **语言** | TypeScript | 5.x | 类型安全 |
| **框架** | Express | 4.x | Web 框架 |
| **ORM** | Prisma | 5.x | 数据库 ORM |
| **数据库** | PostgreSQL | 15.x | 主数据库 |
| **缓存** | Redis | 7.x | 缓存与会话 |
| **验证** | Zod | 3.x | 数据验证 |
| **JWT** | jsonwebtoken | 9.x | Token 管理 |
| **加密** | bcrypt | 5.x | 密码加密 |
| **文件存储** | MinIO | latest | 对象存储 |

### 1.3 基础设施

| 类别 | 技术选型 | 说明 |
|------|---------|------|
| **容器化** | Docker | 容器编排 |
| **编排** | Kubernetes | 生产环境部署 |
| **CI/CD** | GitHub Actions | 自动化部署 |
| **API 网关** | Kong | 路由、限流、认证 |
| **反向代理** | Nginx | 负载均衡 |
| **消息队列** | RabbitMQ | 异步通信 |
| **搜索** | Elasticsearch | 全文搜索 |
| **监控** | Prometheus + Grafana | 指标监控 |
| **日志** | ELK Stack | 日志管理 |
| **追踪** | Jaeger | 分布式追踪 |

---

## 2. 开发环境搭建

### 2.1 前置要求

**必须安装的软件**:

```bash
# Windows (使用 Git Bash 或 WSL)
# macOS (使用 Homebrew)

# 1. Git
git --version  # >= 2.30

# 2. Node.js (推荐使用 nvm 管理版本)
nvm install 20
node --version  # v20.x
npm --version   # >= 10.x

# 3. Docker
docker --version  # >= 20.10
docker-compose --version  # >= 2.0

# 4. PostgreSQL 客户端 (可选)
psql --version  # >= 15

# 5. Redis 客户端 (可选)
redis-cli --version  # >= 7
```

### 2.2 项目初始化

```bash
# 克隆项目
git clone https://github.com/your-org/ctms-edc-iwrs.git
cd ctms-edc-iwrs

# 安装前端依赖
cd apps/web
npm install

# 安装后端依赖
cd ../../services/auth
npm install
# 对其他服务重复此步骤
```

### 2.3 环境变量配置

**后端环境配置** (`.env`):

```bash
# 应用配置
NODE_ENV=development
PORT=3001
SERVER_URL=http://localhost:3001

# 数据库配置
DATABASE_URL=postgresql://admin:password@localhost:5432/ctms_edc

# Redis 配置
REDIS_URL=redis://localhost:6379

# JWT 配置
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRES_IN=1h
JWT_REFRESH_SECRET=your-refresh-secret-key
JWT_REFRESH_EXPIRES_IN=7d

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=ctms-edc

# 加密配置
ENCRYPTION_KEY=your-32-byte-encryption-key

# 日志配置
LOG_LEVEL=debug

# 租户配置（多租户开发）
DEFAULT_TENANT_ID=ten_demo_001
```

**前端环境配置** (`.env`):

```bash
VITE_API_BASE_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080/ws
VITE_APP_TITLE=CTMS+EDC+IWRS 平台
```

### 2.4 Docker Compose 配置

**`docker-compose.yml`**:

```yaml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: ctms_postgres
    environment:
      POSTGRES_DB: ctms_edc
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
      POSTGRES_INITDB_ARGS: '--encoding=UTF-8 --lc-collate=C --lc-ctype=C'
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: ctms_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MinIO (对象存储)
  minio:
    image: minio/minio:latest
    container_name: ctms_minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  # RabbitMQ (消息队列)
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: ctms_rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: password
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx (API 网关)
  nginx:
    image: nginx:alpine
    container_name: ctms_nginx
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
    depends_on:
      - auth-service
      - ctms-service
      - edc-service
      - iwrs-service
    restart: unless-stopped

  # 认证服务
  auth-service:
    build:
      context: ./services/auth
      dockerfile: Dockerfile
    container_name: ctms_auth_service
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://admin:password@postgres:5432/ctms_edc
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./services/auth:/app
      - /app/node_modules
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # CTMS 服务
  ctms-service:
    build:
      context: ./services/ctms
      dockerfile: Dockerfile
    container_name: ctms_ctms_service
    ports:
      - "3002:3002"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://admin:password@postgres:5432/ctms_edc
    volumes:
      - ./services/ctms:/app
      - /app/node_modules
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  # EDC 服务
  edc-service:
    build:
      context: ./services/edc
      dockerfile: Dockerfile
    container_name: ctms_edc_service
    ports:
      - "3003:3003"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://admin:password@postgres:5432/ctms_edc
      - MINIO_ENDPOINT=minio:9000
    volumes:
      - ./services/edc:/app
      - /app/node_modules
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
    restart: unless-stopped

  # IWRS 服务
  iwrs-service:
    build:
      context: ./services/iwrs
      dockerfile: Dockerfile
    container_name: ctms_iwrs_service
    ports:
      - "3004:3004"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://admin:password@postgres:5432/ctms_edc
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./services/iwrs:/app
      - /app/node_modules
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # 前端应用
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: ctms_web
    ports:
      - "3000:3000"
    volumes:
      - ./apps/web:/app
      - /app/node_modules
    depends_on:
      - nginx
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  minio_data:
  rabbitmq_data:
```

---

## 3. 项目结构

```
ctms-edc-iwrs/
├── apps/
│   └── web/                          # 前端应用
│       ├── src/
│       │   ├── components/           # 公共组件
│       │   ├── pages/                # 页面组件
│       │   ├── services/             # API 服务
│       │   ├── stores/               # Zustand 状态
│       │   ├── utils/                # 工具函数
│       │   └── types/                # TypeScript 类型
│       ├── public/
│       ├── package.json
│       ├── tsconfig.json
│       └── vite.config.ts
│
├── services/
│   ├── auth/                         # 认证服务
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   ├── middleware/
│   │   │   ├── routes/
│   │   │   └── index.ts
│   │   ├── prisma/
│   │   │   └── schema.prisma
│   │   ├── package.json
│   │   └── Dockerfile
│   │
│   ├── ctms/                         # CTMS 服务
│   ├── edc/                          # EDC 服务
│   ├── iwrs/                         # IWRS 服务
│   ├── portfolio/                    # 病历夹服务
│   ├── document/                     # 文档服务
│   ├── reporting/                    # 报表服务
│   ├── notification/                 # 通知服务
│   ├── security/                     # 安全服务
│   ├── integration/                  # 集成服务
│   ├── config/                       # 配置服务
│   └── validation/                   # 验证服务
│
├── packages/
│   ├── shared/                       # 共享代码
│   │   ├── types/                    # 共享类型定义
│   │   ├── utils/                    # 共享工具函数
│   │   └── constants/                # 常量定义
│   │
│   └── ui-kit/                       # UI 组件库
│
├── infrastructure/
│   ├── docker/                       # Docker 配置
│   ├── kubernetes/                   # K8s 配置
│   ├── nginx/                        # Nginx 配置
│   └── scripts/                      # 运维脚本
│
├── docs/
│   ├── architecture/                 # 架构文档
│   ├── api/                          # API 文档
│   └── design/                       # 设计文档
│
├── .github/
│   └── workflows/                    # CI/CD 配置
│
├── docker-compose.yml
├── package.json
├── turbo.json                        # Turborepo 配置
├── README.md
└── .gitignore
```

---

## 4. 开发工作流

### 4.1 启动开发环境

```bash
# 1. 启动基础设施（一次即可）
docker-compose up -d postgres redis minio rabbitmq

# 2. 运行数据库迁移
cd services/auth
npx prisma migrate dev
npx prisma generate

# 3. 启动后端服务（每个服务一个终端）
cd services/auth
npm run dev  # 监听端口 3001

# 在新终端
cd services/ctms
npm run dev  # 监听端口 3002

# 4. 启动前端应用
cd apps/web
npm run dev  # 监听端口 3000

# 5. 访问应用
# 前端：http://localhost:3000
# API 网关：http://localhost:8080
```

### 4.2 使用 Turborepo（推荐）

```bash
# 启动所有服务
npm run dev:all

# 构建所有服务
npm run build

# 运行测试
npm run test

# 代码检查
npm run lint
```

### 4.3 数据库操作

```bash
# 创建迁移
npx prisma migrate dev --name init

# 应用迁移
npx prisma migrate deploy

# 生成 Prisma Client
npx prisma generate

# 打开 Prisma Studio
npx prisma studio

# 重置数据库（⚠️ 生产环境慎用）
npx prisma migrate reset
```

---

## 5. CI/CD 配置

### 5.1 GitHub Actions 工作流

**`.github/workflows/ci.yml`**:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  # 代码检查
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run lint
        run: npm run lint

  # 单元测试
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm run test
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}

  # 构建镜像
  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker-compose build
      
      - name: Push to registry
        run: |
          docker login -u ${{ secrets.DOCKER_USER }} -p ${{ secrets.DOCKER_PASSWORD }}
          docker push your-registry/auth-service:latest
          docker push your-registry/ctms-service:latest
          # ...其他服务

  # 部署到生产环境
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f infrastructure/kubernetes/
        env:
          KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
```

---

## 6. 监控与日志

### 6.1 Prometheus 配置

**`infrastructure/prometheus/prometheus.yml`**:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:3001']
    
  - job_name: 'ctms-service'
    static_configs:
      - targets: ['ctms-service:3002']
    
  - job_name: 'edc-service'
    static_configs:
      - targets: ['edc-service:3003']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']
```

### 6.2 日志聚合（ELK Stack）

**`docker-compose.elk.yml`**:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - ELASTIC_PASSWORD=elastic
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5000:5000"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

---

## 7. 性能优化建议

### 7.1 前端优化

```typescript
// 1. 代码分割
const EDCForms = lazy(() => import('./pages/EDCForms'));

// 2. React.memo 优化
const StudyCard = React.memo(({ study }) => {
  return <div>{study.name}</div>;
});

// 3. 虚拟列表（大数据集）
import { VirtualList } from 'react-virtualized';

// 4. API 请求优化
// 使用请求防抖
useDebounce(async () => {
  await fetchStudies();
}, 300);
```

### 7.2 后端优化

```typescript
// 1. Redis 缓存
async function getStudy(studyId: string) {
  const cached = await redis.get(`study:${studyId}`);
  if (cached) return JSON.parse(cached);
  
  const study = await prisma.study.findUnique({ id: studyId });
  await redis.setEx(`study:${studyId}`, 3600, JSON.stringify(study));
  return study;
}

// 2. 数据库查询优化
// 使用 select 只查询需要的字段
const studies = await prisma.study.findMany({
  select: {
    id: true,
    name: true,
    status: true,
  },
  where: { tenant_id: tenantId },
  take: 20,
});

// 3. 数据库索引
// 为常用查询字段创建复合索引
CREATE INDEX idx_studies_tenant_status ON studies(tenant_id, status);
```

### 7.3 数据库优化

```sql
-- 1. 分区表（大数据表）
CREATE TABLE audit_logs_2026_05 (
  CHECK (timestamp >= '2026-05-01' AND timestamp < '2026-06-01')
) INHERITS (audit_logs);

-- 2. 物化视图（复杂查询）
CREATE MATERIALIZED VIEW mv_study_enrollment AS
SELECT 
  s.id,
  s.name,
  COUNT(DISTINCT r.subject_id) as enrolled_count
FROM studies s
JOIN sites sit ON sit.study_id = s.id
JOIN randomizations r ON r.site_id = sit.id
GROUP BY s.id, s.name;

-- 刷新物化视图
REFRESH MATERIALIZED VIEW mv_study_enrollment;
```

---

## 8. 安全最佳实践

### 8.1 密码策略

```typescript
// 密码强度验证
function validatePassword(password: string): boolean {
  const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
  return regex.test(password);
}

// bcrypt 加密（cost=12）
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);
```

### 8.2 API 限流

```typescript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 分钟
  max: 100, // 每窗口最多 100 个请求
  message: '请求过于频繁，请稍后再试'
});

app.use('/api/v1/', limiter);
```

### 8.3 CORS 配置

```typescript
const cors = require('cors');

app.use(cors({
  origin: ['https://your-app.com'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Tenant-ID']
}));
```

---

## 9. 开发规范

### 9.1 Git Commit 规范

```bash
# 格式：<type>(<scope>): <subject>

# type 类型
feat:     新功能
fix:      修复 bug
docs:     文档更新
style:    代码格式（不影响代码运行）
refactor: 重构
test:     测试相关
chore:    构建/辅助工具变动

# 示例
git commit -m "feat(edc): 添加 eCRF 表单设计器"
git commit -m "fix(auth): 修复 JWT 刷新令牌过期问题"
```

### 9.2 代码审查清单

- [ ] 代码符合 TypeScript 严格模式
- [ ] 所有 API 都有输入验证（Zod）
- [ ] 错误处理完善（try-catch + 统一错误格式）
- [ ] 数据库查询已优化（索引、分页）
- [ ] 敏感数据已加密
- [ ] 审计日志已记录
- [ ] 单元测试覆盖核心逻辑
- [ ] API 文档已更新

---

## 10. 下一步行动

1. ✅ **完成技术架构设计文档**
2. ✅ **完成数据库 Schema 设计**
3. ✅ **完成 API 接口规范**
4. ✅ **完成开发环境搭建指南**
5. ⏭️ **执行：搭建开发环境**
   - 安装所有前置软件
   - 配置 Docker Compose
   - 初始化数据库
   - 运行第一个服务
6. ⏭️ **执行：核心服务开发**
   - 认证服务（第 1 周）
   - CTMS 服务（第 2 周）
   - EDC 服务（第 3-4 周）
7. ⏭️ **执行：前端开发**
   - 搭建 React 脚手架
   - 实现核心页面
   - 集成 API

---

**文档结束**

**附录**:
- [微服务架构设计](./1-microservices-architecture.md)
- [数据库 Schema 设计](./2-database-schema.md)
- [API 接口规范](./3-api-specifications.md)
