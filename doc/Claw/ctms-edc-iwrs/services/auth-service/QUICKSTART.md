# Auth Service 快速启动指南

## 🚀 快速开始（5 分钟）

### 1. 安装依赖

```bash
cd services/auth-service
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少配置以下必需项：

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/auth_db?schema=public"
JWT_SECRET="your-super-secret-jwt-key-minimum-32-characters"
```

### 3. 初始化数据库

```bash
# 生成 Prisma Client
npx prisma generate

# 创建数据库迁移
npx prisma migrate dev --name init

# 运行种子脚本（创建默认租户、角色和管理员）
npx prisma db seed
```

### 4. 启动服务

```bash
# 开发模式（自动重启）
npm run dev

# 生产模式
npm start
```

访问 http://localhost:3000/health 确认服务正常运行。

## 🔑 默认登录凭证

Seed 脚本创建了以下默认账户：

```
用户名：admin
邮箱：admin@ctms-platform.com
密码：Admin@123456
角色：超级管理员（super_admin）
```

⚠️ **首次登录后请立即修改密码！**

## 📝 常用命令

```bash
# 数据库操作
npm run prisma:generate    # 生成 Prisma Client
npm run prisma:migrate     # 运行数据库迁移
npm run prisma:studio      # 打开 Prisma Studio（数据库 GUI）
npm run seed               # 运行种子脚本

# 开发
npm run dev                # 启动开发服务器
npm run build              # 编译 TypeScript
npm run type-check         # 类型检查
npm run lint               # ESLint 检查
npm run lint:fix           # 自动修复 ESLint 问题
npm run format             # Prettier 格式化

# 测试
npm test                   # 运行测试
npm run test:coverage      # 运行测试并生成覆盖率报告
npm run test:watch         # 监听模式运行测试
```

## 🧪 测试 API

### 1. 登录

```bash
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123456"
  }'
```

保存返回的 `accessToken`。

### 2. 获取用户资料

```bash
curl http://localhost:3000/api/v1/auth/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 获取用户列表

```bash
curl http://localhost:3000/api/v1/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. 获取角色列表

```bash
curl http://localhost:3000/api/v1/roles \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🐳 Docker 快速启动

### 使用 Docker Compose（推荐）

在项目根目录执行：

```bash
docker-compose up -d postgres redis auth-service
```

### 手动构建和运行

```bash
# 构建镜像
docker build -t ctms-auth-service:latest .

# 运行容器
docker run -d \
  --name auth-service \
  -p 3000:3000 \
  -e DATABASE_URL=postgresql://postgres:postgres@postgres:5432/auth_db \
  -e JWT_SECRET=your-super-secret-jwt-key \
  ctms-auth-service:latest
```

## 📊 数据库管理

### 使用 Prisma Studio 查看数据库

```bash
npx prisma studio
```

浏览器访问 http://localhost:5555 查看和管理数据。

### 常用 SQL 查询

```sql
-- 查看所有租户
SELECT * FROM tenants;

-- 查看所有用户
SELECT * FROM users;

-- 查看所有角色及其权限
SELECT r.*, json_pretty(r.permissions) as permissions 
FROM roles r;

-- 查看用户的角色
SELECT u.username, r.name as role_name, r.permissions
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id;

-- 查看最近的审计日志
SELECT * FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 20;
```

## 🔧 故障排查

### 问题：Prisma Client 生成失败

```bash
# 解决方案：重新安装依赖并生成
npm install
npx prisma generate
```

### 问题：数据库连接失败

检查 PostgreSQL 是否运行：

```bash
# macOS/Linux
pg_isready -h localhost -p 5432

# Windows (PowerShell)
Test-NetConnection -ComputerName localhost -Port 5432
```

### 问题：端口 3000 被占用

修改 `.env` 文件中的端口：

```env
PORT=3001
```

### 问题：JWT 验证失败

确认 JWT_SECRET 至少 32 个字符，并且在 `.env` 和代码中一致。

## 📚 下一步

1. **阅读完整文档**: 查看 [README.md](./README.md) 了解更多 API 详情
2. **查看数据库结构**: `npx prisma studio`
3. **测试所有 API**: 使用 Postman 或 curl 测试所有端点
4. **配置 CORS**: 在 `.env` 中配置 `CORS_ORIGINS`
5. **设置监控**: 集成 Prometheus 和 Grafana

## 🆘 获取帮助

- 查看项目文档：`README.md`
- 查看数据库模式：`prisma/schema.prisma`
- 查看 API 路由：`src/routes/*.ts`
- 查看业务逻辑：`src/services/*.ts`

---

**开发团队**: CTMS+EDC+IWRS Platform Team  
**版本**: 1.0.0  
**更新日期**: 2024-05-27
