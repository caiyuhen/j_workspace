# CTMS/EDC 系统调试启动确认文档

## 环境确认

✅ **PostgreSQL数据库**：已确认本地环境存在并可访问
✅ **项目依赖**：已安装所有必需的npm包
✅ **配置文件**：.env文件配置正确，包含所有必要参数
✅ **调试配置**：VS Code调试配置已创建完成

## 数据库连接配置

根据.env文件配置：
- 数据库URL: `postgresql://postgres:root@123@localhost:5432/ctms_edc?schema=public`
- 数据库名称: `ctms_edc`
- 用户名: `postgres`
- 密码: `root@123`
- 主机: `localhost`
- 端口: `5432`

## 启动前检查清单

1. ✅ PostgreSQL服务正在运行
2. ✅ 项目依赖已安装 (`npm install` 已完成)
3. ✅ 数据库用户和权限配置正确
4. ✅ 环境变量配置无误

## 调试启动步骤

### 1. 启动后端服务（Node.js + TypeScript）
```bash
cd D:/workspace/CTMS_Project/server
npm run dev
```

### 2. 启动前端服务（React + Vite）
```bash
cd D:/workspace/CTMS_Project/client
npm run dev
```

### 3. VS Code调试启动（推荐）
1. 打开VS Code
2. 打开项目文件夹 `D:/workspace/CTMS_Project`
3. 按 `Ctrl+Shift+P` 
4. 选择调试配置：
   - `Launch Server` - 调试后端
   - `Launch Client` - 调试前端  
   - `Launch Full Stack` - 调试完整应用

## 服务访问地址

- **后端API**: `http://localhost:3000`
- **前端页面**: `http://localhost:5173`
- **数据库管理**: Prisma Studio (运行 `npx prisma studio`)

## 调试功能说明

启用调试模式后，您可以：
- 设置断点进行单步调试
- 实时查看变量值
- 检查API响应和错误
- 监控系统性能和日志

## 额外建议

1. 首次启动可能会需要几分钟时间来初始化数据库
2. 如果遇到连接问题，请检查防火墙设置
3. 建议在启动前验证数据库用户和密码配置
4. 可以使用 `npx prisma studio` 查看数据库内容

现在您的系统已准备就绪，可以开始调试会话了。