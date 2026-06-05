# 系统架构与API接口文档

## 1. 系统架构概述

本系统采用微服务架构，所有模块集成于同一数据库中，通过统一认证服务进行用户管理和权限控制。系统包含四个核心模块：

- **CTMS系统**：临床试验管理系统
- **EDC系统**：电子数据采集系统  
- **IWRS系统**：交互式随机化与药物供应管理系统
- **病历夹系统**：医生个人病历夹

## 2. 统一认证服务

### 2.1 认证流程
```
用户登录 -> 认证服务验证 -> 生成JWT令牌 -> 各模块验证令牌
```

### 2.2 API接口

#### POST /api/auth/login
用户登录认证
- 请求体:
```json
{
  "username": "string",
  "password": "string"
}
```
- 响应:
```json
{
  "success": true,
  "token": "jwt_token_string",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string"
  }
}
```

#### POST /api/auth/register
用户注册
- 请求体:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "firstName": "string",
  "lastName": "string"
}
```
- 响应:
```json
{
  "success": true,
  "token": "jwt_token_string",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string"
  }
}
```

## 3. 数据流与权限控制

### 3.1 医生病历夹与EDC系统数据流

#### 正确的数据流向:
```
[EDC系统] --> [病历夹系统]
[EDC模板] --> [病历夹系统]
```

#### 限制的数据流向:
```
[病历夹系统] --禁止--> [EDC系统]
```

### 3.2 数据导入接口

#### POST /api/edc/import-to-patient-folder
将EDC中的患者数据导入到病历夹系统中
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "patientId": "uuid",
  "sourceData": {
    "trialId": "uuid",
    "formData": "json"
  }
}
```
- 响应:
```json
{
  "success": true,
  "message": "数据导入成功",
  "folderId": "uuid"
}
```

#### POST /api/edc/import-template-to-patient-folder
导入EDC模板到病历夹系统
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "templateId": "uuid",
  "folderId": "uuid"
}
```
- 响应:
```json
{
  "success": true,
  "message": "模板导入成功"
}
```

#### GET /api/patient-folder/data/{patientId}
获取病历夹中的患者数据（不支持向EDC反向导入）
- 请求头: `Authorization: Bearer <token>`
- 响应:
```json
{
  "patientId": "uuid",
  "folderData": "json",
  "createdDate": "datetime"
}
```

### 3.3 权限模型

#### 角色定义:
- `admin`: 系统管理员，拥有所有权限
- `researcher`: 研究者，可以访问CTMS和EDC系统
- `crc`: 临床协调员，可以访问EDC系统
- `monitor`: 监查员，可以访问CTMS和EDC系统
- `iwrs_admin`: 随机化管理员，可以访问IWRS系统
- `doctor`: 医生，可以访问病历夹系统
- `patient`: 患者，用于患者的简单访问

#### 权限控制示例:
- EDC系统: 研究者、CRC、监查员可以使用
- CTMS系统: 研究者、监查员、管理员可以使用
- IWRS系统: 随机化管理员可以使用
- 病历夹系统: 医生、管理员可以使用

## 4. 核心模块API接口

### 4.1 CTMS模块接口

#### GET /api/ctms/trials
获取临床试验列表
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `tenantId`: "uuid"
- 响应:
```json
{
  "trials": [
    {
      "id": "uuid",
      "name": "string",
      "status": "string",
      "startDate": "date",
      "endDate": "date"
    }
  ]
}
```

#### POST /api/ctms/trials
创建临床试验
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "name": "string",
  "description": "string",
  "startDate": "date",
  "endDate": "date",
  "status": "string"
}
```

#### GET /api/ctms/trial/{id}
获取特定试验详情
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `tenantId`: "uuid"

#### PUT /api/ctms/trials/{id}
更新试验信息
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "name": "string",
  "description": "string",
  "startDate": "date",
  "endDate": "date",
  "status": "string"
}
```

#### DELETE /api/ctms/trials/{id}
删除试验
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `tenantId`: "uuid"

### 4.2 EDC模块接口

#### GET /api/edc/templates
获取表单模板列表
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `tenantId`: "uuid"
- 响应:
```json
{
  "templates": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "createdAt": "datetime"
    }
  ]
}
```

#### POST /api/edc/templates
创建表单模板
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "name": "string",
  "description": "string",
  "templateData": "json"
}
```

#### GET /api/edc/form-data
获取表单数据
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `patientId`: "uuid"
  - `templateId`: "uuid"
  - `tenantId`: "uuid"

#### POST /api/edc/form-data
提交表单数据
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "trialId": "uuid",
  "patientId": "uuid",
  "templateId": "uuid",
  "data": "json"
}
```

#### GET /api/edc/cdash-fields
获取CDASH字段库
- 请求头: `Authorization: Bearer <token>`
- 响应:
```json
{
  "cdashFields": [
    {
      "variableName": "string",
      "displayLabel": "string",
      "domain": "string",
      "fieldType": "string",
      "sdtmMapping": {
        "domain": "string",
        "variable": "string"
      }
    }
  ]
}
```

### 4.3 IWRS模块接口

#### GET /api/iwrs/randomization-config
获取随机化配置
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `trialId`: "uuid"
  - `tenantId`: "uuid"
- 响应:
```json
{
  "config": {
    "id": "uuid",
    "algorithm": "string",
    "treatmentArms": "json",
    "blockSizes": "json",
    "allocationRatio": "string"
  }
}
```

#### POST /api/iwrs/randomization-config
创建随机化配置
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "trialId": "uuid",
  "algorithm": "string",
  "treatmentArms": "json",
  "blockSizes": "json",
  "allocationRatio": "string"
}
```

#### POST /api/iwrs/patient-randomization
为患者执行随机化
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "patientId": "uuid",
  "trialId": "uuid",
  "treatmentGroup": "string"
}
```

#### GET /api/iwrs/drug-inventory
获取药物库存
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `tenantId`: "uuid"
- 响应:
```json
{
  "inventory": [
    {
      "id": "uuid",
      "drugName": "string",
      "specification": "string",
      "batchNumber": "string",
      "quantity": "integer",
      "expiryDate": "date",
      "location": "string"
    }
  ]
}
```

#### POST /api/iwrs/drug-inventory
添加药物库存
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "drugName": "string",
  "specification": "string",
  "batchNumber": "string",
  "quantity": "integer",
  "expiryDate": "date",
  "location": "string"
}
```

#### GET /api/iwrs/blinding-requests
获取破盲申请
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `tenantId`: "uuid"
  - `status`: "string"
- 响应:
```json
{
  "requests": [
    {
      "id": "uuid",
      "patientId": "uuid",
      "trialId": "uuid",
      "reason": "string",
      "status": "string",
      "createdAt": "datetime"
    }
  ]
}
```

#### POST /api/iwrs/blinding-requests
创建破盲申请
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "patientId": "uuid",
  "trialId": "uuid",
  "reason": "string"
}
```

### 4.4 病历夹模块接口

#### GET /api/patient-folder/patients
获取患者列表
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `tenantId`: "uuid"
- 响应:
```json
{
  "patients": [
    {
      "id": "uuid",
      "patientId": "string",
      "firstName": "string",
      "lastName": "string",
      "dateOfBirth": "date",
      "gender": "string"
    }
  ]
}
```

#### POST /api/patient-folder/patients
创建患者
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "patientId": "string",
  "firstName": "string",
  "lastName": "string",
  "dateOfBirth": "date",
  "gender": "string",
  "contactInfo": "json"
}
```

#### GET /api/patient-folder/folders
获取患者病历夹
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `patientId`: "uuid"
  - `tenantId`: "uuid"
- 响应:
```json
{
  "folders": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "createdAt": "datetime"
    }
  ]
}
```

#### POST /api/patient-folder/folders
创建病历夹
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "patientId": "uuid",
  "name": "string",
  "description": "string"
}
```

#### POST /api/patient-folder/folder-data
添加病历夹数据
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "folderId": "uuid",
  "patientId": "uuid",
  "data": "json"
}
```

#### GET /api/patient-folder/folder-data
获取病历夹数据
- 请求头: `Authorization: Bearer <token>`
- 查询参数:
  - `folderId`: "uuid"
  - `patientId`: "uuid"
  - `tenantId`: "uuid"

#### POST /api/patient-folder/import-template
导入EDC模板到病历夹
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "templateId": "uuid",
  "folderId": "uuid"
}
```

## 5. 多租户支持接口

### 5.1 租户管理

#### GET /api/tenants
获取租户列表
- 请求头: `Authorization: Bearer <token>`
- 响应:
```json
{
  "tenants": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "isActive": "boolean",
      "createdAt": "datetime"
    }
  ]
}
```

#### POST /api/tenants
创建租户
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "name": "string",
  "description": "string"
}
```

#### GET /api/tenants/{id}
获取特定租户详情
- 请求头: `Authorization: Bearer <token>`

#### PUT /api/tenants/{id}
更新租户信息
- 请求头: `Authorization: Bearer <token>`
- 请求体:
```json
{
  "name": "string",
  "description": "string",
  "isActive": "boolean"
}
```

#### DELETE /api/tenants/{id}
删除租户
- 请求头: `Authorization: Bearer <token>`

## 6. 系统监控接口

### 6.1 健康检查
#### GET /health
- 响应:
```json
{
  "status": "OK",
  "service": "monitoring-service",
  "timestamp": "datetime"
}
```

### 6.2 系统指标
#### GET /metrics
- 响应:
```json
{
  "metrics": {
    "database": {
      "patients": "integer",
      "tenants": "integer",
      "users": "integer"
    },
    "services": {
      "auth_service": "string",
      "ctms_service": "string",
      "edc_service": "string",
      "iwrs_service": "string",
      "patient_folder_service": "string",
      "api_gateway": "string"
    },
    "timestamp": "datetime"
  }
}
```

## 7. 安全与合规

### 7.1 数据安全
- 所有传输数据使用HTTPS加密
- 敏感数据如患者姓名、联系方式等使用字段级加密存储
- 支持AES-256和国密SM4加密算法

### 7.2 审计日志
- 记录所有关键操作
- 包括用户登录/登出、数据修改、权限变更、系统配置变更等
- 日志不可篡改，保留期限不少于15年

### 7.3 合规性要求
- 符合21 CFR Part 11要求
- 符合GDPR和HIPAA规定
- 符合CDISC标准