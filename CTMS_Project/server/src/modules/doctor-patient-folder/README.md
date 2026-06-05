# 医生日历夹功能实现说明

## 功能概述
本模块实现医生个人病历夹功能，允许医生创建和管理自己的患者档案，包括患者信息、随访记录和表单模板。此模块与现有的EDC系统独立，遵守以下约束条件：
- EDC数据不导入到医生病历夹
- 病历夹可以引用EDC系统中的表单模板
- 保持所有功能独立性和数据隔离

## 模块结构

```
src/modules/doctor-patient-folder/
├── dto/                    # 数据传输对象
│   ├── patient.dto.ts      # 患者数据验证
│   ├── follow-up.dto.ts    # 随访数据验证
│   └── template.dto.ts     # 模板数据验证
├── entity/                 # 数据库实体
│   ├── patient.entity.ts   # 患者实体
│   ├── follow-up.entity.ts # 随访记录实体
│   └── template.entity.ts  # 表单模板实体
├── service/                # 业务逻辑服务
│   ├── patient.service.ts
│   ├── follow-up.service.ts
│   └── template.service.ts
├── controller/             # 控制器
│   ├── patient.controller.ts
│   ├── follow-up.controller.ts
│   └── template.controller.ts
├── routes/                 # 路由定义
│   └── doctor-folder.routes.ts
├── doctor-patient-folder.module.ts  # 模块配置
└── doctor-patient-folder-feature.module.ts  # 功能模块
```

## 主要特性

### 1. 患者管理
- 创建、查询、更新和删除患者档案
- 支持患者分组和标签管理
- 包含基本患者信息：姓名、性别、出生日期等

### 2. 随访记录
- 记录患者的随访数据
- 支持自定义表单模板引用
- 历史数据跟踪和管理

### 3. 表单模板
- 引用EDC中的现有表单模板
- 模板版本管理和存储
- 与EDC系统保持数据结构一致性

### 4. API接口

#### 患者管理
- `POST /api/doctor-folder/patients` - 创建患者档案
- `GET /api/doctor-folder/patients/:id` - 获取患者详情
- `PUT /api/doctor-folder/patients/:id` - 更新患者档案
- `DELETE /api/doctor-folder/patients/:id` - 删除患者档案
- `GET /api/doctor-folder/patients` - 获取用户所有患者档案

#### 随访记录
- `POST /api/doctor-folder/follow-up` - 创建随访记录
- `GET /api/doctor-folder/follow-up/:id` - 获取随访记录
- `PUT /api/doctor-folder/follow-up/:id` - 更新随访记录
- `DELETE /api/doctor-folder/follow-up/:id` - 删除随访记录
- `GET /api/doctor-folder/follow-up/patient/:patientId` - 获取患者的所有随访记录

#### 表单模板
- `POST /api/doctor-folder/templates` - 创建模板
- `GET /api/doctor-folder/templates` - 获取所有模板
- `GET /api/doctor-folder/templates/:id` - 获取模板详情
- `PUT /api/doctor-folder/templates/:id` - 更新模板
- `DELETE /api/doctor-folder/templates/:id` - 删除模板

## 安全和合规
- 基于JWT的认证和授权
- 所有操作都有审计日志
- 数据访问权限控制，确保用户仅访问自己创建的数据
- 遵循21 CFR Part 11标准