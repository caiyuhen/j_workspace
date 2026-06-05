# CTMS+EDC+IWRS 平台 - API 接口设计规范

**文档版本**: 1.0  
**创建日期**: 2026-05-27  
**作者**: 架构团队  
**状态**: 草案

---

## 1. 设计原则

### 1.1 RESTful 原则

- **资源导向**: 使用名词表示资源，避免动词
- **HTTP 方法**: GET (查询)、POST (创建)、PUT (更新)、DELETE (删除)、PATCH (部分更新)
- **状态码**: 使用标准 HTTP 状态码
- **版本控制**: URL 路径版本控制 (`/api/v1/`)
- **幂等性**: GET、PUT、DELETE 操作必须幂等

### 1.2 统一响应格式

```json
// 成功响应
{
  "success": true,
  "data": { /* 业务数据 */ },
  "message": "操作成功",
  "request_id": "req_123456789"
}

// 分页响应
{
  "success": true,
  "data": {
    "items": [/* 数据列表 */],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "request_id": "req_123456789"
}

// 错误响应
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": [
      { "field": "email", "message": "邮箱格式不正确" }
    ]
  },
  "request_id": "req_123456789"
}
```

### 1.3 错误码规范

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `SUCCESS` | 200 | 操作成功 |
| `BAD_REQUEST` | 400 | 请求参数错误 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 禁止访问 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `VALIDATION_ERROR` | 422 | 验证失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

---

## 2. 认证服务 API (Auth Service)

**Base URL**: `https://api.example.com/api/v1/auth`

### 2.1 用户登录

```
POST /login
```

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "remember_me": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "def50200...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "usr_123",
      "email": "user@example.com",
      "name": "张三",
      "roles": ["data_manager", "site_coordinator"]
    }
  }
}
```

### 2.2 刷新令牌

```
POST /refresh
```

**Request**:
```json
{
  "refresh_token": "def50200..."
}
```

### 2.3 获取用户信息

```
GET /profile
```

**Headers**: `Authorization: Bearer <access_token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "usr_123",
    "tenant_id": "ten_456",
    "email": "user@example.com",
    "name": "张三",
    "phone": "13800138000",
    "avatar_url": "https://...",
    "roles": [
      {
        "id": "role_1",
        "name": "数据管理员",
        "code": "data_manager",
        "permissions": ["edc:read", "edc:write", "report:read"]
      }
    ],
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

### 2.4 企业微信 SSO

```
POST /sso/wechat
```

**Request**:
```json
{
  "code": "wechat_auth_code",
  "state": "state_token"
}
```

---

## 3. CTMS 服务 API (CTMS Service)

**Base URL**: `https://api.example.com/api/v1/ctms`

### 3.1 试验管理

#### 3.1.1 列出试验

```
GET /studies
```

**Query Parameters**:
- `page` (number, default: 1)
- `page_size` (number, default: 20)
- `status` (string, optional)
- `search` (string, optional)

**Response**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "std_123",
        "study_number": "CTMS-2026-001",
        "name": "乳腺癌新药 III 期临床试验",
        "status": "recruiting",
        "target_enrollment": 200,
        "actual_enrollment": 45,
        "start_date": "2026-01-01",
        "created_at": "2025-12-01T00:00:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

#### 3.1.2 创建试验

```
POST /studies
```

**Request**:
```json
{
  "study_number": "CTMS-2026-002",
  "name": "新药临床试验项目",
  "description": "研究 XX 药物的疗效",
  "study_type": "interventional",
  "design": "RCT",
  "sponsor": "XX 制药公司",
  "principal_investigator": "李四",
  "target_enrollment": 100,
  "start_date": "2026-06-01"
}
```

#### 3.1.3 获取试验详情

```
GET /studies/:id
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "std_123",
    "study_number": "CTMS-2026-001",
    "name": "乳腺癌新药 III 期临床试验",
    "protocol_id": "pro_456",
    "description": "...",
    "study_type": "interventional",
    "design": "RCT",
    "sponsor": "XX 制药",
    "status": "recruiting",
    "target_enrollment": 200,
    "actual_enrollment": 45,
    "sites": [
      {
        "id": "sit_001",
        "site_number": "S001",
        "name": "北京协和医院",
        "pi_name": "张三",
        "actual_enrollment": 20
      }
    ],
    "enrollment_progress": {
      "total": 45,
      "target": 200,
      "percentage": 22.5
    }
  }
}
```

### 3.2 研究中心管理

#### 3.2.1 列出研究中心

```
GET /studies/:studyId/sites
```

**Query Parameters**:
- `status` (string, optional)
- `page`, `page_size`

#### 3.2.2 添加研究中心

```
POST /studies/:studyId/sites
```

**Request**:
```json
{
  "site_number": "S005",
  "name": "上海瑞金医院",
  "address": "上海市瑞金二路 197 号",
  "city": "上海",
  "pi_name": "王五",
  "pi_email": "wangwu@hospital.com",
  "target_enrollment": 30
}
```

### 3.3 工时管理

#### 3.3.1 提交工时

```
POST /timesheets
```

**Request**:
```json
{
  "study_id": "std_123",
  "site_id": "sit_001",
  "date": "2026-05-27",
  "hours": 8.5,
  "task_type": "data_entry",
  "description": "录入患者访视数据"
}
```

#### 3.3.2 审批工时

```
POST /timesheets/:id/approve
```

**Request**:
```json
{
  "approved": true,
  "notes": "工时记录无误"
}
```

---

## 4. EDC 服务 API (EDC Service)

**Base URL**: `https://api.example.com/api/v1/edc`

### 4.1 eCRF 模板管理

#### 4.1.1 列出模板

```
GET /templates
```

**Query Parameters**:
- `study_id` (string, required)
- `status` (string, optional)

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "tpl_001",
      "study_id": "std_123",
      "name": "不良事件表",
      "code": "ae_form",
      "cdash_compliant": true,
      "version": "1.2",
      "status": "active"
    }
  ]
}
```

#### 4.1.2 创建模板

```
POST /templates
```

**Request**:
```json
{
  "study_id": "std_123",
  "name": "生命体征表",
  "code": "vital_signs",
  "structure": {
    "sections": [
      {
        "id": "sec_1",
        "title": "生命体征",
        "fields": [
          {
            "key": "sbp",
            "label": "收缩压",
            "type": "number",
            "unit": "mmHg",
            "cdash_variable": "VSSBP1",
            "required": true,
            "validation": {
              "min": 80,
              "max": 250
            }
          },
          {
            "key": "dbp",
            "label": "舒张压",
            "type": "number",
            "unit": "mmHg",
            "cdash_variable": "VSDBP1",
            "required": true
          }
        ]
      }
    ]
  }
}
```

### 4.2 数据录入

#### 4.2.1 获取表单

```
GET /forms/:studyId/:subjectId/:templateId
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "frm_789",
    "subject_id": "SV001",
    "template_id": "tpl_001",
    "visit_name": "筛选期",
    "form_data": {
      "ae_term": "头痛",
      "ae_start_date": "2026-05-20",
      "ae_severity": "mild"
    },
    "status": "draft"
  }
}
```

#### 4.2.2 提交数据

```
POST /data
```

**Request**:
```json
{
  "study_id": "std_123",
  "site_id": "sit_001",
  "subject_id": "SV001",
  "template_id": "tpl_001",
  "visit_name": "筛选期",
  "form_data": {
    "ae_term": "头痛",
    "ae_start_date": "2026-05-20",
    "ae_severity": "mild",
    "ae_outcome": "resolved"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "form_id": "frm_789",
    "validation_results": {
      "passed": true,
      "warnings": [],
      "errors": []
    }
  }
}
```

### 4.3 质疑管理

#### 4.3.1 发起质疑

```
POST /queries
```

**Request**:
```json
{
  "study_id": "std_123",
  "form_id": "frm_789",
  "field_key": "ae_start_date",
  "query_type": "manual",
  "question": "请确认不良事件开始日期是否正确？"
}
```

#### 4.3.2 回复质疑

```
POST /queries/:id/reply
```

**Request**:
```json
{
  "answer": "已确认，日期正确",
  "resolved": true
}
```

---

## 5. IWRS 服务 API (IWRS Service)

**Base URL**: `https://api.example.com/api/v1/iwrs`

### 5.1 随机化配置

#### 5.1.1 配置随机化方案

```
POST /config
```

**Request**:
```json
{
  "study_id": "std_123",
  "algorithm": "stratified",
  "treatment_arms": [
    { "id": "arm_1", "name": "试验药 A", "dose": "100mg" },
    { "id": "arm_2", "name": "安慰剂", "dose": "0mg" }
  ],
  "stratification_factors": [
    {
      "name": "研究中心",
      "values": ["S001", "S002", "S003"]
    },
    {
      "name": "疾病分期",
      "values": ["II 期", "III 期"]
    }
  ],
  "allocation_ratio": [1, 1],
  "block_sizes": [4, 6]
}
```

### 5.2 患者随机化

#### 5.2.1 执行随机化

```
POST /randomize
```

**Request**:
```json
{
  "study_id": "std_123",
  "site_id": "sit_001",
  "subject_id": "SV00123",
  "stratification_values": {
    "研究中心": "S001",
    "疾病分期": "II 期"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "randomization_id": "RND20260527001",
    "subject_id": "SV00123",
    "treatment_arm": "试验药 A",
    "drug_package": "PKG-001",
    "randomized_at": "2026-05-27T11:00:00Z",
    "message": "随机化成功，请核对药物包装"
  }
}
```

#### 5.2.2 查询随机化状态

```
GET /:subjectId
```

**Response**:
```json
{
  "success": true,
  "data": {
    "subject_id": "SV00123",
    "randomization_id": "RND20260527001",
    "is_blinded": true,
    "randomized_at": "2026-05-27T11:00:00Z",
    "visit_status": "screening"
  }
}
```

### 5.3 紧急破盲

#### 5.3.1 破盲申请

```
POST /unblind
```

**Request**:
```json
{
  "randomization_id": "RND20260527001",
  "reason": "患者出现严重不良反应，需紧急破盲"
}
```

#### 5.3.2 破盲审批

```
POST /unblind/:id/approve
```

**Request**:
```json
{
  "approved": true,
  "notes": "情况紧急，同意破盲"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "treatment_arm": "试验药 A",
    "drug_package": "PKG-001",
    "unblinded_at": "2026-05-27T12:00:00Z"
  }
}
```

---

## 6. 安全服务 API (Security Service)

**Base URL**: `https://api.example.com/api/v1/security`

### 6.1 审计追踪

#### 6.1.1 查询审计日志

```
GET /audit/logs
```

**Query Parameters**:
- `entity_type` (string, optional)
- `entity_id` (string, optional)
- `user_id` (string, optional)
- `start_time` (datetime, optional)
- `end_time` (datetime, optional)
- `page`, `page_size`

**Response**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "aud_001",
        "entity_type": "Study",
        "entity_id": "std_123",
        "action": "UPDATE",
        "old_value": { "status": "planning" },
        "new_value": { "status": "recruiting" },
        "user_id": "usr_456",
        "user_name": "张三",
        "ip_address": "192.168.1.100",
        "timestamp": "2026-05-27T10:30:00Z"
      }
    ],
    "total": 100
  }
}
```

---

## 7. 通用规范

### 7.1 请求头 (Headers)

```
Authorization: Bearer <access_token>
X-Tenant-ID: <tenant_id>
X-Request-ID: <unique_request_id>
Content-Type: application/json
Accept: application/json
```

### 7.2 分页参数

```
?page=1&page_size=20&sort=created_at&order=desc
```

### 7.3 过滤参数

```
?status=active&study_id=std_123&created_at_gte=2026-01-01
```

### 7.4 字段选择

```
?fields=id,name,status,created_at
```

---

## 8. OpenAPI 规范示例

```yaml
openapi: 3.0.0
info:
  title: CTMS+EDC+IWRS API
  version: 1.0.0
  description: 临床试验管理平台 API 文档

servers:
  - url: https://api.example.com/api/v1

paths:
  /studies:
    get:
      summary: 列出试验
      tags:
        - Studies
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedStudies'
    
    post:
      summary: 创建试验
      tags:
        - Studies
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateStudyRequest'
      responses:
        '201':
          description: 创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Study'

components:
  schemas:
    Study:
      type: object
      properties:
        id:
          type: string
        study_number:
          type: string
        name:
          type: string
        status:
          type: string
          enum: ['planning', 'approved', 'recruiting', 'active', 'completed', 'terminated']
    
    PaginatedStudies:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Study'
        total:
          type: integer
        page:
          type: integer
        page_size:
          type: integer
```

---

**文档结束**

**下一步**:
- 生成 OpenAPI YAML 文件
- 使用 OpenAPI Generator 生成客户端 SDK
- 创建 API Mock 服务
