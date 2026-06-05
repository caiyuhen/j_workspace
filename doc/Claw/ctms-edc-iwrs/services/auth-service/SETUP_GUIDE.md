# Auth Service 设置与启动指南

## 📋 前置条件检查

### 必需软件

- ✅ **Node.js 20+** - 已确认安装 (v22.22.2)
- ⚠️ **PostgreSQL 14+** - 需要安装
- ⚠️ **Redis 7+** (可选) - 需要安装（用于会话管理和限流）

### 当前状态

```
✅ Node.js: v22.22.2
✅ npm: v10.9.7
❌ PostgreSQL: 未安装
❌ Redis: 未安装
❌ Docker: 未安装
❌ Dependencies: 未安装
```

---

## 🚀 快速启动方案

### 方案 A: 使用 Docker（推荐）

这是最简单的方式，一次性启动所有服务：

1. **安装 Docker Desktop**
   - Windows: https://www.docker.com/products/docker-desktop/
   - 安装后重启电脑

2. **启动数据库和 Redis**
   ```bash
   # 在项目根目录执行
   cd D:\workspace\doc\Claw\ctms-edc-iwrs
   docker-compose up -d postgres redis
   ```

3. **等待数据库就绪**
   ```bash
   # 等待 10 秒让数据库初始化
   timeout /t 10
   ```

4. **安装依赖并初始化数据库**
   ```bash
   cd services\auth-service
   npm install
   npx prisma generate
   npx prisma migrate dev --name init
   npx prisma db seed
   ```

5. **启动服务**
   ```bash
   npm run dev
   ```

---

### 方案 B: 本地安装（手动）

#### 步骤 1: 安装 PostgreSQL

**Windows 安装步骤：**

1. 下载 PostgreSQL 14/15/16
   - 官方下载：https://www.postgresql.org/download/windows/
   - 或使用 pgAdmin 安装包

2. 安装时记录：
   - PostgreSQL 端口（默认 5432）
   - 用户名（默认 postgres）
   - 密码（建议设置简单密码用于开发）

3. 验证安装
   ```bash
   # 检查服务是否运行
   pg_ctl status
   
   # 或使用 pgAdmin 连接测试
   ```

4. 创建数据库
   ```bash
   # 使用 psql 命令行
   psql -U postgres
   
   # 在 SQL 提示符下执行
   CREATE DATABASE auth_db;
   \q
   ```

#### 步骤 2: 安装 Redis（可选）

**Windows 安装：**

1. 下载 Windows Redis 端口
   ```bash
   # 使用 Chocolatey（如果已安装）
   choco install redis-64
   
   # 或手动下载
   # https://github.com/microsoftarchive/redis/releases
   ```

2. 启动 Redis
   ```bash
   # 作为服务启动
   redis-server --service-start
   
   # 或手动启动
   redis-server
   ```

3. 验证 Redis
   ```bash
   redis-cli ping
   # 应该返回: PONG
   ```

#### 步骤 3: 配置环境变量

编辑 `.env.development` 文件：

```bash
# 复制模板
cp .env.example .env

# 或使用已创建的开发环境文件
cp .env.development .env
```

**修改以下配置：**

```env
# 数据库连接（根据你的 PostgreSQL 配置修改）
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/auth_db?schema=public"

# JWT 密钥（开发环境可以用这个，生产环境必须更换）
JWT_SECRET=ctms-auth-super-secret-key-2024-development-minimum-32-chars

# Redis（如果安装了）
REDIS_URL="redis://localhost:6379"
```

#### 步骤 4: 安装依赖

```bash
cd D:\workspace\doc\Claw\ctms-edc-iwrs\services\auth-service
npm install
```

#### 步骤 5: 初始化数据库

```bash
# 生成 Prisma Client
npx prisma generate

# 创建数据库迁移
npx prisma migrate dev --name init

# 运行种子脚本（创建默认数据）
npx prisma db seed
```

**预期输出：**
```
🌱 Starting database seed...
🏢 Creating default tenant...
✅ Tenant created: Default Organization (uuid)
🎭 Creating default roles...
✅ Role created: 超级管理员
✅ Role created: 管理员
✅ Role created: 研究员
✅ Role created: 监查员
✅ Role created: 观察员
👤 Creating default admin user...
✅ User created: admin (admin@ctms-platform.com)
🔗 Assigning roles...
✅ Role assigned: super_admin → admin
✨ Database seed completed successfully!
```

#### 步骤 6: 启动服务

```bash
# 开发模式（自动重启）
npm run dev

# 或编译后运行
npm run build
npm start
```

**预期输出：**
```
info: Auth Service is running on port 3000
info: Environment: development
info: Health check: http://localhost:3000/health
info: Ready check: http://localhost:3000/ready
info: API Docs: http://localhost:3000/api/v1
```

---

## ✅ 验证安装

### 1. 健康检查

```bash
curl http://localhost:3000/health
```

**预期响应：**
```json
{
  "success": true,
  "service": "auth-service",
  "version": "1.0.0",
  "timestamp": "2024-05-29T01:44:17.123Z",
  "status": "healthy"
}
```

### 2. 测试登录

```bash
# Windows PowerShell
$body = @{
    username = "admin"
    password = "Admin@123456"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/v1/auth/login" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

**或使用在线工具：**
- Postman
- Bruno
- httpie

**预期响应：**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": "uuid",
      "username": "admin",
      "email": "admin@ctms-platform.com",
      "firstName": "系统",
      "lastName": "管理员",
      "tenantId": "uuid",
      "roles": ["super_admin"]
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 604800
  }
}
```

### 3. 查看数据库

```bash
# 使用 Prisma Studio 可视化查看数据库
npx prisma studio
```

浏览器访问 http://localhost:5555 可以看到：
- 默认租户
- 5 个角色及其权限
- 管理员账户
- 审计日志

---

## 🔧 常见问题解决

### 问题 1: PostgreSQL 连接失败

**错误信息：**
```
Error: P1001: Can't reach database server
```

**解决方案：**
1. 检查 PostgreSQL 服务是否运行
   ```bash
   # Windows
   pg_ctl status
   
   # 启动服务
   pg_ctl -D "C:\Program Files\PostgreSQL\14\data" start
   ```

2. 验证数据库是否存在
   ```bash
   psql -U postgres -c "\l"
   ```

3. 检查 DATABASE_URL 配置是否正确

### 问题 2: Prisma 迁移失败

**错误信息：**
```
Error: The database 'auth_db' does not exist
```

**解决方案：**
```bash
# 手动创建数据库
psql -U postgres
CREATE DATABASE auth_db;
\q

# 重新运行迁移
npx prisma migrate dev
```

### 问题 3: 端口被占用

**错误信息：**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**解决方案：**
```bash
# 修改 .env 文件
PORT=3001
```

### 问题 4: JWT 验证失败

**错误信息：**
```
Error: jwt malformed
```

**解决方案：**
- 确保 JWT_SECRET 至少 32 个字符
- 检查 .env 文件是否正确加载
- 重启服务

---

## 📚 下一步

### 成功启动后，你可以：

1. **探索 API**
   - 阅读完整的 [API 文档](./README.md)
   - 使用 Postman 测试所有端点
   - 查看数据库中的数据

2. **开发新功能**
   - 添加新的权限
   - 创建自定义角色
   - 实现 2FA 认证

3. **集成到项目**
   - 配置其他服务连接 Auth Service
   - 实现单点登录（SSO）
   - 设置 API 网关

4. **性能优化**
   - 集成 Redis 缓存
   - 配置连接池
   - 添加监控

---

## 🆘 获取帮助

- **查看日志**: `logs/app.log`
- **数据库管理**: `npx prisma studio`
- **API 测试**: 使用 Postman 或 curl
- **代码结构**: 查看 [DEVELOPMENT_STATUS.md](./DEVELOPMENT_STATUS.md)

---

**默认登录凭证：**
```
用户名：admin
密码：Admin@123456
角色：超级管理员
```

⚠️ **首次登录后请立即修改密码！**

---

*文档版本：1.0.0*  
*更新日期：2024-05-29*  
*维护团队：CTMS+EDC+IWRS Platform Team*
