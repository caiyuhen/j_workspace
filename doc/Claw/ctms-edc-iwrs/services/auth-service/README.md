# Auth Service

CTMS+EDC+IWRS 平台的核心认证与授权服务，提供单点登录、RBAC 权限管理和多租户支持。

## 🎯 功能特性

- ✅ **JWT 无状态认证** - 双 token 策略（access token + refresh token）
- ✅ **RBAC 权限模型** - 细粒度的资源操作权限控制
- ✅ **多租户支持** - 数据隔离，每个租户独立的用户体系
- ✅ **账户安全** - 登录失败锁定、强密码策略、会话管理
- ✅ **21 CFR Part 11 合规** - 完整的审计追踪、不可篡改日志
- ✅ **密码找回** - 基于邮箱的密码重置流程
- ✅ **RESTful API** - 标准化的 HTTP 接口设计

## 🏗️ 技术栈

- **Runtime**: Node.js 20+
- **Framework**: Express.js
- **ORM**: Prisma
- **Database**: PostgreSQL
- **Validation**: Zod
- **Security**: Helmet, CORS, Rate Limiting
- **Logging**: Winston
- **Password Hashing**: bcryptjs
- **JWT**: jsonwebtoken

## 📋 前提条件

- Node.js 20+ 和 npm
- PostgreSQL 14+
- Redis 7+（可选，用于会话管理和限流）

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等
```

### 3. 初始化数据库

```bash
# 生成 Prisma Client
npx prisma generate

# 运行数据库迁移
npx prisma migrate dev

# 初始化默认数据（租户、角色、管理员账户）
npx prisma db seed
```

### 4. 启动服务

```bash
# 开发模式
npm run dev

# 生产模式
npm start
```

服务将在 `http://localhost:3000` 启动。

### 5. 健康检查

```bash
curl http://localhost:3000/health
curl http://localhost:3000/ready
```

## 📚 API 文档

### 认证接口

#### 1. 用户注册

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "john.doe",
  "email": "john@example.com",
  "password": "StrongPass@123",
  "displayName": "John Doe"
}
```

#### 2. 用户登录

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "Admin@123456",
  "rememberMe": true
}

# Response
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": "uuid",
      "username": "admin",
      "email": "admin@ctms-platform.com",
      "displayName": "系统管理员",
      "tenantId": "uuid",
      "roles": ["super_admin"]
    },
    "accessToken": "eyJhbG...",
    "refreshToken": "eyJhbG...",
    "expiresIn": 604800
  }
}
```

#### 3. 刷新令牌

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refreshToken": "eyJhbG...",
  "tenantId": "uuid"
}
```

#### 4. 登出

```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbG...
```

#### 5. 获取用户资料

```http
GET /api/v1/auth/profile
Authorization: Bearer eyJhbG...
```

#### 6. 修改密码

```http
POST /api/v1/auth/change-password
Authorization: Bearer eyJhbG...
Content-Type: application/json

{
  "currentPassword": "OldPass@123",
  "newPassword": "NewPass@456"
}
```

#### 7. 忘记密码

```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "admin@ctms-platform.com"
}
```

#### 8. 重置密码

```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "newPassword": "NewPass@456"
}
```

### 用户管理接口（管理员）

#### 1. 获取用户列表

```http
GET /api/v1/users?page=1&limit=20&search=john&status=ACTIVE
Authorization: Bearer eyJhbG...
```

#### 2. 获取用户详情

```http
GET /api/v1/users/:userId
Authorization: Bearer eyJhbG...
```

#### 3. 更新用户信息

```http
PUT /api/v1/users/:userId
Authorization: Bearer eyJhbG...
Content-Type: application/json

{
  "email": "new.email@example.com",
  "displayName": "New Name"
}
```

#### 4. 更新用户状态

```http
PUT /api/v1/users/:userId/status
Authorization: Bearer eyJhbG...
Content-Type: application/json

{
  "status": "SUSPENDED"
}
```

#### 5. 删除用户

```http
DELETE /api/v1/users/:userId
Authorization: Bearer eyJhbG...
```

### 角色管理接口（管理员）

#### 1. 创建角色

```http
POST /api/v1/roles
Authorization: Bearer eyJhbG...
Content-Type: application/json

{
  "name": "data_manager",
  "displayName": "数据管理员",
  "description": "负责数据管理和质控",
  "permissions": [
    "data:read",
    "data:update",
    "query:create",
    "query:update"
  ]
}
```

#### 2. 获取角色列表

```http
GET /api/v1/roles
Authorization: Bearer eyJhbG...
```

#### 3. 分配角色给用户

```http
POST /api/v1/roles/:roleId/assign
Authorization: Bearer eyJhbG...
Content-Type: application/json

{
  "userId": "uuid-of-user"
}
```

#### 4. 撤销用户角色

```http
DELETE /api/v1/roles/:roleId/revoke
Authorization: Bearer eyJhbG...
Content-Type: application/json

{
  "userId": "uuid-of-user"
}
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t ctms-auth-service:latest .
```

### 运行容器

```bash
docker run -d \
  --name auth-service \
  -p 3000:3000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/auth_db \
  -e JWT_SECRET=your-secret-key \
  ctms-auth-service:latest
```

### Docker Compose

使用根目录的 `docker-compose.yml` 启动完整环境：

```bash
# 在根目录执行
docker-compose up -d auth-service postgres redis
```

## 🔐 安全配置

### 密码策略

- 最小长度：12 个字符
- 必须包含：大写字母、小写字母、数字、特殊字符
- 密码哈希：bcrypt（12 rounds）

### 账户锁定策略

- 最大登录失败次数：5 次
- 锁定时长：15 分钟
- 自动解锁

### JWT 配置

- Access Token 有效期：7 天
- Refresh Token 有效期：30 天
- 签发者：ctms-auth-service
- 受众：ctms-platform

### CORS 配置

在 `.env` 中配置允许的源：

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://app.ctms.com
```

## 🗄️ 数据库架构

### 核心表

- **tenants** - 租户信息
- **users** - 用户账户
- **roles** - 角色定义
- **user_roles** - 用户角色关联
- **sessions** - 用户会话
- **audit_logs** - 审计日志
- **refresh_tokens** - 刷新令牌
- **password_reset_tokens** - 密码重置令牌

### 查看数据库

```bash
npx prisma studio
```

## 🧪 测试

```bash
# 运行单元测试
npm test

# 运行测试覆盖率
npm run test:cov

# 运行 ESLint
npm run lint

# 运行类型检查
npm run type-check
```

## 📊 默认账户

Seed 脚本会创建以下默认数据：

### 租户
- **代码**: default
- **名称**: Default Organization

### 角色
1. **super_admin** - 超级管理员（全部权限）
2. **admin** - 管理员（大部分管理权限）
3. **researcher** - 研究员（数据录入和管理）
4. **monitor** - 监查员（数据核查和质量控制）
5. **viewer** - 观察员（只读权限）

### 管理员账户
- **用户名**: admin
- **邮箱**: admin@ctms-platform.com
- **密码**: Admin@123456
- **角色**: super_admin

⚠️ **首次登录后请立即修改密码！**

## 📝 审计日志

所有敏感操作都会被记录到 `audit_logs` 表：

- 用户登录/登出
- 密码修改
- 用户创建/更新/删除
- 角色分配/撤销
- 数据访问（可选）

审计日志符合 **21 CFR Part 11** 要求：
- 时间戳（带时区）
- 操作用户
- 操作类型
- 操作对象
- 变更前后的值
- IP 地址和用户代理
- 不可篡改

## 🔧 开发指南

### 项目结构

```
auth-service/
├── prisma/
│   ├── schema.prisma       # 数据库模式定义
│   └── seed.ts             # 数据库初始化脚本
├── src/
│   ├── config/
│   │   └── index.ts        # 配置管理
│   ├── controllers/
│   │   ├── auth.controller.ts
│   │   ├── user.controller.ts
│   │   └── role.controller.ts
│   ├── dto/
│   │   └── auth.dto.ts     # 请求验证模式
│   ├── middleware/
│   │   ├── auth.ts         # 认证中间件
│   │   └── authorization.ts # 授权中间件
│   ├── services/
│   │   ├── auth.service.ts
│   │   ├── user.service.ts
│   │   └── role.service.ts
│   ├── utils/
│   │   ├── jwt.ts          # JWT 工具
│   │   ├── logger.ts       # 日志工具
│   │   └── prisma.ts       # Prisma 客户端
│   └── index.ts            # 应用入口
├── .env.example            # 环境变量模板
├── Dockerfile              # Docker 构建配置
├── package.json
└── README.md
```

### 添加新的 API 端点

1. 在 `dto/auth.dto.ts` 中定义请求验证模式
2. 在 `services/*.ts` 中添加业务逻辑
3. 在 `controllers/*.ts` 中添加控制器方法
4. 在 `routes/*.ts` 中注册路由
5. 在 `index.ts` 中挂载路由

### 调试模式

```bash
# 使用 nodemon 自动重启
npm run dev

# 使用 debugger
NODE_ENV=development node --inspect dist/index.js
```

## 📖 参考资料

- [Prisma 文档](https://www.prisma.io/docs)
- [Express.js 指南](https://expressjs.com/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc7519)
- [21 CFR Part 11](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-signatures-final-rule)
- [OAuth 2.0](https://oauth.net/2/)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用内部许可证。详见公司知识产权政策。

## 👥 团队

- **架构设计**: CTMS Platform Team
- **开发**: Backend Team
- **维护**: DevOps Team

---

© 2024 CTMS+EDC+IWRS Platform. All rights reserved.
