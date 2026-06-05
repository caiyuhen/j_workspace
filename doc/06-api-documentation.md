# 医疗临床试验平台 - API 接口详细文档

## 一、API 设计规范

### 1.1 RESTful API 规范

```
基础 URL: https://api.clinical-trial-platform.com/api/v1

请求方法:
- GET: 获取资源
- POST: 创建资源
- PUT: 更新资源（全量更新）
- PATCH: 更新资源（部分更新）
- DELETE: 删除资源

统一响应格式:
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": 1234567890
}

错误响应格式:
{
  "code": 400,
  "message": "Bad Request",
  "errors": [
    {
      "field": "username",
      "message": "用户名已存在"
    }
  ],
  "timestamp": 1234567890
}
```

### 1.2 认证与授权

```
认证方式：JWT (JSON Web Token)

请求头:
Authorization: Bearer <token>

Token 结构:
{
  "sub": "user-id",
  "tenant_id": "tenant-uuid",
  "username": "user@example.com",
  "roles": ["role1", "role2"],
  "exp": 1234567890
}

权限校验:
- 租户隔离：所有接口自动过滤 tenant_id
- 角色权限：基于 RBAC 的权限控制
- 数据权限：基于角色的数据访问限制
```

### 1.3 版本管理

```
API 版本: /api/v1/

向后兼容策略:
- 不删除旧版本接口
- 至少保留 2 个主要版本
- 废弃接口提前 6 个月通知
```

---

## 二、认证授权 API

### 2.1 用户登录

```yaml
POST /api/v1/auth/login
```

**请求参数:**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "tenantCode": "TENANT001"
}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "Bearer",
    "expiresIn": 86400,
    "userInfo": {
      "userId": "uuid-here",
      "username": "user@example.com",
      "realName": "张三",
      "roles": ["data_manager"],
      "tenantId": "tenant-uuid"
    }
  },
  "timestamp": 1234567890
}
```

**错误响应:**
```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "timestamp": 1234567890
}
```

### 2.2 刷新 Token

```yaml
POST /api/v1/auth/refresh
```

**请求参数:**
```json
{
  "refreshToken": "refresh-token-here"
}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "new-token-here",
    "refreshToken": "new-refresh-token-here",
    "expiresIn": 86400
  },
  "timestamp": 1234567890
}
```

### 2.3 登出

```yaml
POST /api/v1/auth/logout
```

**请求头:**
```
Authorization: Bearer <token>
```

**响应参数:**
```json
{
  "code": 200,
  "message": "登出成功",
  "timestamp": 1234567890
}
```

### 2.4 获取当前用户信息

```yaml
GET /api/v1/auth/me
```

**请求头:**
```
Authorization: Bearer <token>
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "userId": "uuid-here",
    "username": "user@example.com",
    "email": "user@example.com",
    "realName": "张三",
    "phone": "13800138000",
    "avatarUrl": "https://cdn.example.com/avatar.jpg",
    "roles": [
      {
        "roleId": "role-uuid",
        "roleCode": "data_manager",
        "roleName": "数据管理员",
        "permissions": ["form:read", "form:write", "data:read"]
      }
    ],
    "tenant": {
      "tenantId": "tenant-uuid",
      "tenantCode": "TENANT001",
      "tenantName": "某医药公司",
      "subscriptionTier": "professional"
    },
    "lastLoginAt": "2026-01-15T10:30:00Z"
  },
  "timestamp": 1234567890
}
```

### 2.5 修改密码

```yaml
PUT /api/v1/auth/change-password
```

**请求头:**
```
Authorization: Bearer <token>
```

**请求参数:**
```json
{
  "oldPassword": "old-password",
  "newPassword": "new-password",
  "confirmPassword": "new-password"
}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "密码修改成功",
  "timestamp": 1234567890
}
```

**错误响应:**
```json
{
  "code": 400,
  "message": "旧密码错误",
  "timestamp": 1234567890
}
```

---

## 三、CTMS 模块 API

### 3.1 试验项目管理

#### 3.1.1 创建试验

```yaml
POST /api/v1/trials
```

**请求头:**
```
Authorization: Bearer <token>
```

**请求参数:**
```json
{
  "trialCode": "TRIAL2026001",
  "trialName": "某药物Ⅲ期临床试验",
  "protocolNumber": "PROT-2026-001",
  "sponsorName": "某制药公司",
  "phase": "III",
  "therapeuticArea": "心血管",
  "startDate": "2026-03-01",
  "endDate": "2027-03-01",
  "budget": 5000000,
  "config": {
    "autoAssignSite": true,
    "requireEthicsApproval": true
  }
}
```

**响应参数:**
```json
{
  "code": 201,
  "message": "试验创建成功",
  "data": {
    "trialId": "trial-uuid",
    "trialCode": "TRIAL2026001",
    "trialName": "某药物Ⅲ期临床试验",
    "status": "planning",
    "createdAt": "2026-01-15T10:30:00Z"
  },
  "timestamp": 1234567890
}
```

#### 3.1.2 获取试验列表

```yaml
GET /api/v1/trials
```

**请求头:**
```
Authorization: Bearer <token>
```

**请求参数:**
```
?phase=III&status=active&pageSize=20&page=1
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "trialId": "trial-uuid",
        "trialCode": "TRIAL2026001",
        "trialName": "某药物Ⅲ期临床试验",
        "phase": "III",
        "sponsorName": "某制药公司",
        "status": "active",
        "startDate": "2026-03-01",
        "endDate": "2027-03-01",
        "enrolledCount": 45,
        "targetEnrollment": 200,
        "progress": 22.5
      }
    ],
    "total": 10,
    "page": 1,
    "pageSize": 20
  },
  "timestamp": 1234567890
}
```

#### 3.1.3 获取试验详情

```yaml
GET /api/v1/trials/{trialId}
```

**请求头:**
```
Authorization: Bearer <token>
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "trialId": "trial-uuid",
    "trialCode": "TRIAL2026001",
    "trialName": "某药物Ⅲ期临床试验",
    "protocolNumber": "PROT-2026-001",
    "sponsorName": "某制药公司",
    "phase": "III",
    "therapeuticArea": "心血管",
    "description": "试验描述...",
    "startDate": "2026-03-01",
    "endDate": "2027-03-01",
    "budget": 5000000,
    "status": "active",
    "manager": {
      "userId": "user-uuid",
      "realName": "张三",
      "email": "zhangsan@example.com"
    },
    "config": {
      "autoAssignSite": true,
      "requireEthicsApproval": true
    },
    "createdAt": "2026-01-15T10:30:00Z",
    "updatedAt": "2026-01-15T10:30:00Z"
  },
  "timestamp": 1234567890
}
```

#### 3.1.4 更新试验

```yaml
PUT /api/v1/trials/{trialId}
```

**请求头:**
```
Authorization: Bearer <token>
```

**请求参数:**
```json
{
  "trialName": "某药物Ⅲ期临床试验（更新）",
  "status": "active",
  "endDate": "2027-06-01",
  "config": {
    "autoAssignSite": false
  }
}
```

#### 3.1.5 删除试验

```yaml
DELETE /api/v1/trials/{trialId}
```

**请求头:**
```
Authorization: Bearer <token>
```

**响应参数:**
```json
{
  "code": 200,
  "message": "试验删除成功",
  "timestamp": 1234567890
}
```

### 3.2 研究中心管理

#### 3.2.1 创建研究中心

```yaml
POST /api/v1/trials/{trialId}/sites
```

**请求参数:**
```json
{
  "siteCode": "SITE001",
  "siteName": "北京协和医院",
  "hospitalName": "北京协和医院",
  "address": "北京市东城区帅府园 1 号",
  "city": "北京",
  "province": "北京",
  "country": "中国",
  "contactPerson": "李医生",
  "contactPhone": "13800138000",
  "contactEmail": "liyi@pumch.cn",
  "gcpCertificate": "GCP2025001",
  "gcpExpiry": "2030-01-01",
  "enrollmentTarget": 50
}
```

#### 3.2.2 获取研究中心列表

```yaml
GET /api/v1/trials/{trialId}/sites
```

**请求参数:**
```
?status=approved&page=1&pageSize=20
```

### 3.3 eTMF 文档管理

#### 3.3.1 上传文档

```yaml
POST /api/v1/trials/{trialId}/etmf/documents
Content-Type: multipart/form-data
```

**表单字段:**
```
documentName: 试验方案.pdf
documentType: Protocol
category: Core Documents
file: [file]
```

**响应参数:**
```json
{
  "code": 201,
  "message": "文档上传成功",
  "data": {
    "documentId": "doc-uuid",
    "documentName": "试验方案.pdf",
    "fileSize": 1048576,
    "uploadedAt": "2026-01-15T10:30:00Z"
  },
  "timestamp": 1234567890
}
```

#### 3.3.2 下载文档

```yaml
GET /api/v1/trials/{trialId}/etmf/documents/{documentId}/download
```

**响应:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="试验方案.pdf"
```

#### 3.3.3 审批文档

```yaml
POST /api/v1/trials/{trialId}/etmf/documents/{documentId}/approve
```

**请求参数:**
```json
{
  "approved": true,
  "approvalNotes": "已审核，同意发布"
}
```

### 3.4 工时管理

#### 3.4.1 填报工时

```yaml
POST /api/v1/work-hours
```

**请求参数:**
```json
{
  "trialId": "trial-uuid",
  "projectTask": "eCRF 表单设计",
  "workDate": "2026-01-15",
  "hours": 8.0,
  "workType": "开发",
  "notes": "完成了 EDC 表单设计器的开发"
}
```

#### 3.4.2 获取工时列表

```yaml
GET /api/v1/work-hours
```

**请求参数:**
```
?trialId=trial-uuid&workDate=2026-01-15&page=1&pageSize=20
```

---

## 四、EDC 模块 API

### 4.1 表单设计

#### 4.1.1 创建表单

```yaml
POST /api/v1/trials/{trialId}/forms
```

**请求参数:**
```json
{
  "formCode": "SUBJ_INFO",
  "formName": "受试者基本信息",
  "formType": "questionnaire",
  "description": "采集受试者基本信息",
  "displayOrder": 1,
  "layoutConfig": {
    "columns": 2,
    "pageSize": "A4"
  }
}
```

#### 4.1.2 获取表单列表

```yaml
GET /api/v1/trials/{trialId}/forms
```

**请求参数:**
```
?version=1.0&is_active=true&page=1&pageSize=20
```

#### 4.1.3 获取表单详情

```yaml
GET /api/v1/forms/{formId}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "formId": "form-uuid",
    "formCode": "SUBJ_INFO",
    "formName": "受试者基本信息",
    "version": "1.0",
    "formType": "questionnaire",
    "is_active": true,
    "displayOrder": 1,
    "fields": [
      {
        "fieldId": "field-uuid",
        "fieldCode": "SUBJID",
        "fieldName": "受试者编号",
        "fieldType": "text",
        "required": true,
        "maxLength": 12,
        "validationPattern": "^[A-Z0-9]{6,12}$",
        "cdashDomain": "DM",
        "sdtmVariable": "SUBJID"
      },
      {
        "fieldId": "field-uuid-2",
        "fieldCode": "AGE",
        "fieldName": "年龄",
        "fieldType": "number",
        "required": true,
        "minValue": 18,
        "maxValue": 85
      }
    ],
    "validationRules": [
      {
        "ruleId": "rule-uuid",
        "ruleType": "required",
        "targetFields": ["SUBJID"],
        "errorMessage": "受试者编号不能为空"
      }
    ],
    "cdashMapping": {
      "domain": "DM",
      "variables": {
        "SUBJID": { "cdash": "SUBJID", "sdtm": "SUBJID" },
        "AGE": { "cdash": "AGE", "sdtm": "AGE" }
      }
    },
    "createdAt": "2026-01-15T10:30:00Z",
    "updatedAt": "2026-01-15T10:30:00Z"
  },
  "timestamp": 1234567890
}
```

#### 4.1.4 更新表单字段

```yaml
PUT /api/v1/forms/{formId}/fields/{fieldId}
```

**请求参数:**
```json
{
  "fieldName": "年龄（更新）",
  "required": true,
  "minValue": 18,
  "maxValue": 90,
  "validationPattern": "^[0-9]+$"
}
```

#### 4.1.5 发布表单

```yaml
POST /api/v1/forms/{formId}/publish
```

**请求参数:**
```json
{
  "version": "1.1",
  "versionNotes": "修改年龄范围为 18-90 岁"
}
```

### 4.2 访视管理

#### 4.2.1 创建访视

```yaml
POST /api/v1/trials/{trialId}/visits
```

**请求参数:**
```json
{
  "visitCode": "V1",
  "visitName": "访视 1",
  "visitDayMin": 1,
  "visitDayMax": 7,
  "isMandatory": true,
  "displayOrder": 1,
  "formIds": ["form-uuid-1", "form-uuid-2"]
}
```

#### 4.2.2 获取访视列表

```yaml
GET /api/v1/trials/{trialId}/visits
```

### 4.3 受试者管理

#### 4.3.1 创建受试者

```yaml
POST /api/v1/trials/{trialId}/subjects
```

**请求参数:**
```json
{
  "siteId": "site-uuid",
  "subjectCode": "SUBJ001",
  "gender": "M",
  "dateOfBirth": "1985-01-01",
  "ethnicity": "Han"
}
```

#### 4.3.2 获取受试者列表

```yaml
GET /api/v1/trials/{trialId}/subjects
```

**请求参数:**
```
?siteId=site-uuid&status=enrolled&page=1&pageSize=20
```

#### 4.3.3 获取受试者详情

```yaml
GET /api/v1/trials/{trialId}/subjects/{subjectId}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "subjectId": "subject-uuid",
    "subjectCode": "SUBJ001",
    "status": "enrolled",
    "gender": "M",
    "dateOfBirth": "1985-01-01",
    "ethnicity": "Han",
    "site": {
      "siteId": "site-uuid",
      "siteCode": "SITE001",
      "siteName": "北京协和医院"
    },
    "randomization": {
      "randomizationDate": "2026-02-01",
      "randomizationNum": "R001",
      "treatmentArm": "Treatment A"
    },
    "visits": [
      {
        "visitId": "visit-uuid",
        "visitCode": "V1",
        "visitDate": "2026-02-05",
        "status": "completed"
      }
    ],
    "createdAt": "2026-01-20T10:00:00Z"
  },
  "timestamp": 1234567890
}
```

#### 4.3.4 入组受试者

```yaml
POST /api/v1/trials/{trialId}/subjects/{subjectId}/enroll
```

**请求参数:**
```json
{
  "screenDate": "2026-01-20",
  "screenFailReason": null,
  "siteId": "site-uuid"
}
```

### 4.4 表单数据提交

#### 4.4.1 提交表单数据

```yaml
POST /api/v1/subject-visits/{visitRecordId}/forms/{formId}/submit
```

**请求参数:**
```json
{
  "data": {
    "SUBJID": "SUBJ001",
    "AGE": 35,
    "SEX": "M",
    "WEIGHT": 70.5,
    "HEIGHT": 175.0
  },
  "notes": "数据录入完成"
}
```

**响应参数:**
```json
{
  "code": 201,
  "message": "表单数据提交成功",
  "data": {
    "dataId": "data-uuid",
    "status": "submitted",
    "submittedAt": "2026-01-20T14:30:00Z"
  },
  "timestamp": 1234567890
}
```

#### 4.4.2 保存草稿

```yaml
POST /api/v1/subject-visits/{visitRecordId}/forms/{formId}/draft
```

**请求参数:**
```json
{
  "data": {
    "SUBJID": "SUBJ001",
    "AGE": 35
  }
}
```

#### 4.4.3 获取表单数据

```yaml
GET /api/v1/subject-visits/{visitRecordId}/forms/{formId}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "dataId": "data-uuid",
    "formId": "form-uuid",
    "formVersion": "1.0",
    "status": "submitted",
    "data": {
      "SUBJID": "SUBJ001",
      "AGE": 35,
      "SEX": "M",
      "WEIGHT": 70.5,
      "HEIGHT": 175.0
    },
    "submittedAt": "2026-01-20T14:30:00Z",
    "submittedBy": {
      "userId": "user-uuid",
      "realName": "张三"
    }
  },
  "timestamp": 1234567890
}
```

### 4.5 数据验证与疑问

#### 4.5.1 验证表单数据

```yaml
POST /api/v1/forms/validate
```

**请求参数:**
```json
{
  "formId": "form-uuid",
  "formData": {
    "SUBJID": "SUBJ001",
    "AGE": 35
  }
}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "验证成功",
  "data": {
    "isValid": true,
    "errors": [],
    "warnings": [
      {
        "field": "AGE",
        "message": "年龄超出常规范围"
      }
    ]
  },
  "timestamp": 1234567890
}
```

#### 4.5.2 创建疑问

```yaml
POST /api/v1/queries
```

**请求参数:**
```json
{
  "trialId": "trial-uuid",
  "subjectId": "subject-uuid",
  "visitRecordId": "visit-uuid",
  "formId": "form-uuid",
  "fieldCode": "AGE",
  "queryTitle": "年龄异常",
  "queryDescription": "受试者年龄 150 岁，超出正常范围",
  "priority": "high",
  "assignedTo": "reviewer-user-uuid"
}
```

#### 4.5.3 处理疑问

```yaml
PUT /api/v1/queries/{queryId}
```

**请求参数:**
```json
{
  "status": "resolved",
  "resolutionNotes": "受试者年龄录入错误，应为 50 岁",
  "responseNotes": "已确认，感谢反馈"
}
```

---

## 五、IWRS 模块 API

### 5.1 随机化方案配置

#### 5.1.1 创建随机化方案

```yaml
POST /api/v1/trials/{trialId}/randomization/schemes
```

**请求参数:**
```json
{
  "schemeName": "Ⅲ期试验随机化方案",
  "schemeType": "block",
  "treatmentArms": [
    {
      "armCode": "ARM_A",
      "armName": "试验组 A",
      "drugCode": "DRUG_A",
      "allocationRatio": 1
    },
    {
      "armCode": "ARM_B",
      "armName": "对照组",
      "drugCode": "DRUG_B",
      "allocationRatio": 1
    }
  ],
  "blockSizes": [4, 6, 8],
  "stratificationFactors": [
    {
      "factorCode": "SITE",
      "factorName": "研究中心",
      "levels": ["SITE001", "SITE002", "SITE003"]
    }
  ]
}
```

#### 5.1.2 获取随机化方案

```yaml
GET /api/v1/trials/{trialId}/randomization/schemes
```

### 5.2 随机化请求

#### 5.2.1 执行随机化

```yaml
POST /api/v1/trials/{trialId}/randomization/requests
```

**请求参数:**
```json
{
  "siteId": "site-uuid",
  "subjectId": "subject-uuid",
  "stratificationFactors": {
    "SITE": "SITE001"
  }
}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "随机化成功",
  "data": {
    "requestId": "request-uuid",
    "randomizationNum": "R001",
    "treatmentArm": "ARM_A",
    "drugAllocation": {
      "drugCode": "DRUG_A",
      "packaging": "Packaging-A-001",
      "quantity": 30
    },
    "requestedAt": "2026-02-01T10:30:00Z",
    "ipAddress": "192.168.1.100"
  },
  "timestamp": 1234567890
}
```

#### 5.2.2 获取随机化结果

```yaml
GET /api/v1/randomization/requests/{requestId}
```

### 5.3 药物管理

#### 5.3.1 配置药物

```yaml
POST /api/v1/trials/{trialId}/drugs
```

**请求参数:**
```json
{
  "drugCode": "DRUG_A",
  "drugName": "试验药物 A",
  "drugType": "drug",
  "packaging": "30 粒/盒",
  "storageCondition": "常温保存",
  "expiryDays": 730
}
```

#### 5.3.2 查询库存

```yaml
GET /api/v1/trials/{trialId}/drugs/inventory
```

**请求参数:**
```
?siteId=site-uuid&drugCode=DRUG_A
```

---

## 六、医生病历夹模块 API

### 6.1 患者病历管理

#### 6.1.1 创建患者病历

```yaml
POST /api/v1/patients
```

**请求参数:**
```json
{
  "patientName": "患者张三",
  "idCard": "110101198501011234",
  "gender": "M",
  "dateOfBirth": "1985-01-01",
  "phone": "13800138000",
  "address": "北京市朝阳区 xx 街道",
  "medicalHistory": "高血压病史 5 年",
  "allergyHistory": "青霉素过敏",
  "familyHistory": "家族无遗传病史"
}
```

#### 6.1.2 获取患者列表

```yaml
GET /api/v1/patients
```

**请求参数:**
```
?name=张三&status=active&page=1&pageSize=20
```

### 6.2 自定义表单

#### 6.2.1 创建自定义表单

```yaml
POST /api/v1/patients/forms
```

**请求参数:**
```json
{
  "formName": "随访表单",
  "formCode": "FOLLOWUP_001",
  "sourceCrfFormId": "crf-form-uuid",
  "fieldsConfig": [
    {
      "fieldCode": "BP_SYS",
      "fieldName": "收缩压",
      "fieldType": "number",
      "required": true,
      "unit": "mmHg"
    },
    {
      "fieldCode": "BP_DIA",
      "fieldName": "舒张压",
      "fieldType": "number",
      "required": true,
      "unit": "mmHg"
    }
  ]
}
```

#### 6.2.2 获取表单列表

```yaml
GET /api/v1/patients/forms
```

### 6.3 表单数据

#### 6.3.1 提交表单数据

```yaml
POST /api/v1/patients/{patientId}/forms/{formId}/submit
```

**请求参数:**
```json
{
  "visitDate": "2026-02-01",
  "data": {
    "BP_SYS": 120,
    "BP_DIA": 80
  }
}
```

#### 6.3.2 获取表单数据

```yaml
GET /api/v1/patients/{patientId}/forms/{formId}
```

### 6.4 检查结果

#### 6.4.1 录入实验室检查

```yaml
POST /api/v1/patients/{patientId}/lab-results
```

**请求参数:**
```json
{
  "resultDate": "2026-02-01",
  "testName": "空腹血糖",
  "testCode": "GLU",
  "resultValue": "5.6 mmol/L",
  "resultNumeric": 5.6,
  "normalRange": "3.9-6.1 mmol/L",
  "abnormalFlag": "N",
  "testType": "blood",
  "facilityName": "检验科"
}
```

#### 6.4.2 录入影像检查

```yaml
POST /api/v1/patients/{patientId}/imaging-results
```

**请求参数:**
```json
{
  "imagingDate": "2026-02-01",
  "imagingType": "CT",
  "bodyPart": "胸部",
  "finding": "双肺未见明显异常",
  "impression": "胸部 CT 未见异常",
  "facilityName": "放射科"
}
```

---

## 七、CDISC 导出 API

### 7.1 生成 SDTM 数据集

```yaml
POST /api/v1/trials/{trialId}/export/sdtm
```

**请求参数:**
```json
{
  "domains": ["DM", "AE", "LB", "EX", "DS"],
  "includeDefine": true,
  "compression": true
}
```

**响应参数:**
```json
{
  "code": 202,
  "message": "导出任务已提交",
  "data": {
    "exportId": "export-uuid",
    "status": "processing",
    "submittedAt": "2026-02-01T10:30:00Z",
    "estimatedCompletion": "2026-02-01T10:35:00Z"
  },
  "timestamp": 1234567890
}
```

### 7.2 查询导出状态

```yaml
GET /api/v1/exports/{exportId}
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "exportId": "export-uuid",
    "status": "completed",
    "exportType": "SDTM",
    "domains": ["DM", "AE", "LB", "EX", "DS"],
    "fileUrl": "https://cdn.example.com/exports/SDTM_TRIAL2026001.zip",
    "fileSize": 5242880,
    "completedAt": "2026-02-01T10:34:30Z"
  },
  "timestamp": 1234567890
}
```

### 7.3 下载 Define.xml

```yaml
GET /api/v1/exports/{exportId}/define.xml
```

**响应:**
```
Content-Type: application/xml
Content-Disposition: attachment; filename="define.xml"
```

---

## 八、审计与监控 API

### 8.1 获取审计日志

```yaml
GET /api/v1/audit-trail
```

**请求参数:**
```
?entityType=form_data&entityId=data-uuid&createdAfter=2026-01-01&page=1&pageSize=20
```

### 8.2 获取系统健康状态

```yaml
GET /api/v1/health
```

**响应参数:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-02-01T10:30:00Z",
    "components": {
      "database": "healthy",
      "cache": "healthy",
      "messageQueue": "healthy"
    }
  },
  "timestamp": 1234567890
}
```

---

## 九、错误码定义

```yaml
通用错误码:
200: 成功
201: 创建成功
202: 处理中
400: 请求参数错误
401: 未授权
403: 禁止访问
404: 资源不存在
409: 资源冲突
422: 数据验证失败
500: 服务器内部错误

业务错误码:
1001: 租户不存在
1002: 用户不存在
1003: 试验不存在
1004: 表单不存在
1005: 受试者不存在
1006: 研究中心不存在
2001: 表单版本已发布，不能修改
2002: 受试者已随机化，不能修改
2003: 数据已被锁定，不能修改
2004: 表单提交失败
2005: 随机化请求失败
3001: 数据验证失败
3002: SDTM 验证失败
3003: CDASH 映射错误
```

---

## 十、API 使用示例

### 10.1 Node.js 客户端示例

```javascript
const axios = require('axios');

class ClinicalTrialAPIClient {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
    this.client = axios.create({
      baseURL: baseURL,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  }
  
  // 获取试验列表
  async getTrials(params) {
    const response = await this.client.get('/trials', { params });
    return response.data;
  }
  
  // 创建试验
  async createTrial(trialData) {
    const response = await this.client.post('/trials', trialData);
    return response.data;
  }
  
  // 提交表单数据
  async submitFormData(visitRecordId, formId, formData) {
    const response = await this.client.post(
      `/subject-visits/${visitRecordId}/forms/${formId}/submit`,
      { data: formData }
    );
    return response.data;
  }
}

// 使用示例
const client = new ClinicalTrialAPIClient(
  'https://api.clinical-trial-platform.com/api/v1',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
);

async function example() {
  // 获取试验列表
  const trials = await client.getTrials({ page: 1, pageSize: 20 });
  console.log('试验列表:', trials);
  
  // 创建试验
  const newTrial = await client.createTrial({
    trialCode: 'TRIAL2026001',
    trialName: '某药物Ⅲ期临床试验',
    phase: 'III',
    sponsorName: '某制药公司'
  });
  console.log('创建试验:', newTrial);
  
  // 提交表单数据
  const submitResult = await client.submitFormData(
    'visit-uuid',
    'form-uuid',
    {
      SUBJID: 'SUBJ001',
      AGE: 35,
      SEX: 'M'
    }
  );
  console.log('提交结果:', submitResult);
}
```

### 10.2 Python 客户端示例

```python
import requests
from typing import Dict, List, Optional

class ClinicalTrialAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.base_url}{endpoint}"
        kwargs['headers'] = {**self.headers, **kwargs.get('headers', {})}
        
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def get_trials(self, page: int = 1, page_size: int = 20) -> Dict:
        """获取试验列表"""
        params = {'page': page, 'pageSize': page_size}
        return self._request('GET', '/trials', params=params)
    
    def create_trial(self, trial_data: Dict) -> Dict:
        """创建试验"""
        return self._request('POST', '/trials', json=trial_data)
    
    def submit_form_data(self, visit_record_id: str, form_id: str, 
                        form_data: Dict) -> Dict:
        """提交表单数据"""
        payload = {'data': form_data}
        endpoint = f'/subject-visits/{visit_record_id}/forms/{form_id}/submit'
        return self._request('POST', endpoint, json=payload)
    
    def export_sdtm(self, trial_id: str, 
                   domains: List[str] = None) -> Dict:
        """导出 SDTM 数据集"""
        payload = {
            'domains': domains or ['DM', 'AE', 'LB', 'EX', 'DS'],
            'includeDefine': True,
            'compression': True
        }
        endpoint = f'/trials/{trial_id}/export/sdtm'
        return self._request('POST', endpoint, json=payload)

# 使用示例
if __name__ == '__main__':
    client = ClinicalTrialAPIClient(
        'https://api.clinical-trial-platform.com/api/v1',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    )
    
    # 获取试验列表
    trials = client.get_trials()
    print('试验列表:', trials)
    
    # 创建试验
    new_trial = client.create_trial({
        'trialCode': 'TRIAL2026001',
        'trialName': '某药物Ⅲ期临床试验',
        'phase': 'III',
        'sponsorName': '某制药公司'
    })
    print('创建试验:', new_trial)
    
    # 导出 SDTM
    export_task = client.export_sdtm('trial-uuid')
    print('导出任务:', export_task)
```

---

## 十一、API 版本历史

### v1.0.0 (2026 年 1 月)
- 初始版本
- 认证授权
- CTMS 核心功能
- EDC 核心功能
- IWRS 核心功能
- 医生病历夹
- CDISC 导出

### v1.1.0 (计划)
- 移动端适配
- 实时通知
- 高级报表
- 数据导入/导出优化

---

*文档版本：v1.0*
*创建日期：2026 年*
*维护人：蔡宇恒*
