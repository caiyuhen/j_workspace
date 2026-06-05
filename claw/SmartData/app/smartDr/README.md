# 临床试验管理系统 (CTMS/EDC/IWRS/Patient Folder)

## 项目概述

这是一个一体化的临床试验管理系统，整合了四个核心模块：
- **CTMS** (Clinical Trial Management System) - 临床试验管理系统
- **EDC** (Electronic Data Capture) - 电子数据采集系统
- **IWRS** (Interactive Web Randomization System) - 交互式随机化与药物供应管理系统
- **医生个人病历夹** - 患者数据管理与随访系统

所有模块运行在同一数据库下，通过统一认证服务进行统一管理，实现了模块间的数据集成与安全控制。

## 系统特性

### 1. 统一数据库架构
- 所有模块共用同一个PostgreSQL数据库
- 采用CDISC标准数据模型
- 行级安全控制（RLS）确保数据隔离

### 2. 统一认证与权限管理
- 统一认证服务（JWT + OAuth2）
- 基于角色的访问控制（RBAC）
- 多租户支持
- 详细的审计追踪

### 3. 模块化设计
- 微服务架构，各模块可独立部署
- 清晰的模块边界和接口定义
- 支持系统扩展与定制

### 4. 安全合规
- 符合21 CFR Part 11
- 符合GDPR和HIPAA
- 支持AES-256和国密SM4加密
- 完整的电子签名支持

## 项目结构

```
smartDr/
├── backend/                # 后端服务
│   ├── auth-service/       # 统一认证服务
│   ├── ctms-service/       # CTMS服务
│   ├── edc-service/        # EDC服务
│   ├── iwrs-service/       # IWRS服务
│   ├── patient-folder-service/ # 病历夹服务
│   ├── api-gateway/        # API网关
│   ├── monitoring-service/ # 监控服务
│   └── common/             # 公共组件
├── frontend/               # 前端页面
│   ├── auth/               # 统一登录页面
│   ├── ctms/               # CTMS登录页面
│   ├── edc/                # EDC登录页面
│   ├── iwrs/               # IWRS登录页面
│   └── patient-folder/     # 病历夹登录页面
├── api/                    # API文档
│   └── docs/               # 系统架构和API文档
├── config/                 # 配置文件
│   └── database/           # 数据库配置
├── deploy/                 # 部署脚本
├── docker-compose.yml      # Docker编排文件
├── Dockerfile              # Docker构建文件
└── nginx/                  # Nginx配置
    └── nginx.conf          # 反向代理配置
```

## 数据流向与权限控制

### 正确的数据流向:
```
[EDC系统] --> [病历夹系统]     (患者数据导入)
[EDC模板] --> [病历夹系统]     (模板导入)
```

### 限制的数据流向:
```
[病历夹系统] --禁止--> [EDC系统]  (数据不可反向导入)
```

## 认证与权限模型

### 用户角色:
- `admin`: 系统管理员
- `researcher`: 研究者
- `crc`: 临床协调员
- `monitor`: 监查员
- `iwrs_admin`: 随机化管理员
- `doctor`: 医生
- `patient`: 患者

### 权限控制:
- 基于角色的细粒度权限控制
- 数据级别的访问控制
- 审计追踪记录所有关键操作

## 技术栈

### 后端:
- Node.js + Express.js
- PostgreSQL
- JWT
- bcrypt.js
- Docker

### 前端:
- HTML5 + CSS3 + JavaScript
- 响应式设计

### 安全:
- HTTPS加密传输
- 数据库字段级加密
- 审计追踪系统
- 多租户支持

## 系统架构

### 服务架构
```
[客户端] --> [API网关] --> [认证服务]
                   |
    [CTMS服务] <--|--> [EDC服务] 
    [IWRS服务] <--|--> [病历夹服务]
    [监控服务] <--|
```

## 部署方式

### 本地开发
1. 在项目根目录运行 `npm install`
2. 启动数据库
3. 启动所有服务

### Docker方式
1. 确保已安装Docker和Docker Compose
2. 在项目根目录执行: `docker-compose up`
3. 系统将在 http://localhost 启动

### 生产部署
1. 配置环境变量
2. 部署Docker容器
3. 配置Nginx反向代理
4. 配置SSL证书

## 开发计划

### Phase 1 - 基础设施与认证 (已完成)
- 数据库设计和部署
- 统一认证服务
- 基础权限系统

### Phase 2 - 核心功能开发 (已完成)
- CTMS和EDC核心功能
- 模块间数据交互接口
- 基础表单设计器

### Phase 3 - 增强功能开发 (已完成)
- IWRS系统
- 病历夹系统
- 安全与审计功能

### Phase 4 - 系统集成与部署 (已完成)
- 多租户支持
- SaaS化部署
- API文档
- 监控告警系统

## 贡献者

蔡宇衡 (Cai Yuheng)
caiyuheng81@outlook.com

## 许可证

MIT License