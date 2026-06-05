# 医学智能体系统 - 启动指南

## 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL (可选，用于生产环境)

## 快速启动

### 1. 安装后端依赖

```bash
cd d:\workspace\SOLO\backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
copy .env.example .env
```

主要配置项：
- `LLM_ENDPOINT`: 大模型服务地址 (默认: http://192.168.0.214:8802/chat/)
- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: JWT密钥

### 3. 初始化数据库 (可选)

如果使用PostgreSQL：

```bash
python scripts/init_db.py
```

### 4. 启动后端服务

```bash
cd d:\workspace\SOLO\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端API文档: http://localhost:8000/docs

### 5. 安装前端依赖

```bash
cd d:\workspace\SOLO\frontend
npm install
```

### 6. 启动前端服务

```bash
cd d:\workspace\SOLO\frontend
npm run dev
```

前端界面: http://localhost:3000

## 测试LLM连接

```bash
cd d:\workspace\SOLO\backend
python scripts/test_llm_connection.py
```

## 默认账户

- 管理员: admin@medical.ai / admin123
- 医生: doctor@medical.ai / doctor123
- 研究员: researcher@medical.ai / researcher123

## 项目结构

```
d:\workspace\SOLO\
├── backend/                # 后端服务
│   ├── app/
│   │   ├── api/v1/        # API端点
│   │   ├── agents/        # 代理实现
│   │   ├── core/          # 核心模块
│   │   ├── models/        # 数据模型
│   │   └── services/      # 服务层
│   ├── scripts/           # 脚本
│   └── requirements.txt   # Python依赖
├── frontend/              # 前端服务
│   ├── src/
│   │   ├── pages/        # 页面组件
│   │   ├── layouts/      # 布局组件
│   │   ├── services/     # API服务
│   │   └── stores/       # 状态管理
│   └── package.json      # Node依赖
└── docker-compose.yml    # Docker配置
```

## API端点

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | POST /api/v1/auth/login | 用户登录 |
| 认证 | POST /api/v1/auth/register | 用户注册 |
| 对话 | GET /api/v1/conversations | 对话列表 |
| 对话 | POST /api/v1/conversations/chat | 发送消息 |
| 代理 | GET /api/v1/agents | 代理列表 |
| 代理 | POST /api/v1/agents/dispatch | 任务调度 |
| 技能 | GET /api/v1/skills | 技能列表 |
| 技能 | POST /api/v1/skills/{id}/execute | 执行技能 |

## 故障排除

### 后端启动失败

1. 检查Python版本: `python --version`
2. 检查依赖安装: `pip list`
3. 检查端口占用: `netstat -ano | findstr :8000`

### 前端启动失败

1. 检查Node版本: `node --version`
2. 删除node_modules重新安装:
   ```bash
   rmdir /s /q node_modules
   npm install
   ```

### LLM连接失败

1. 检查网络连接: `ping 192.168.0.214`
2. 检查服务状态: 访问 http://192.168.0.214:8802
