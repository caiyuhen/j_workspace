# CTMS (临床试验管理系统)

一个符合 GCP 规范且就绪于 21 CFR Part 11 标准的临床试验管理系统。

## 功能特性
- **项目管理**：试验项目、中心、研究者管理。
- **受试者管理**：筛选、入组、访视、ICF（知情同意书）追踪。
- **安全性管理**：AE/SAE 报告、SUSAR 标记。
- **监查管理**：监查报告（SIV 启动访视、RMV 常规访视、COV 关闭访视）、方案违背。
- **文档管理**：带版本控制的 TMF（试验主文档）管理。
- **合规性**：审计追踪（django-simple-history）、RBAC（基于角色的访问控制）。

## 技术栈
- **后端**：Django 5.1, Django REST Framework, PostgreSQL (或开发环境用 SQLite)。
- **前端**：React 18, TypeScript, Vite, Material UI。
- **文档**：Swagger/OpenAPI, Markdown 验证计划。

## 安装说明

### 后端
1. 进入 `CTMS_Code` 目录：
   ```bash
   cd CTMS_Code
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行数据库迁移：
   ```bash
   python manage.py migrate
   ```
4. 创建超级用户（如果需要）：
   ```bash
   python manage.py createsuperuser
   ```
5. 启动服务器：
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   API 文档：http://localhost:8000/swagger/

### 前端
1. 进入 `ctms_frontend` 目录：
   ```bash
   cd ctms_frontend
   ```
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
   访问应用：http://localhost:5173/

## 验证
- 运行测试：`pytest`
- 查看验证计划：`docs/Validation_Plan.md`
- 查看 GCP 检查清单：`docs/GCP_Compliance_Checklist.md`
