# 微服务架构设计

## 1. 服务边界定义

### 1.1 服务拆分原则

基于**领域驱动设计（DDD）**和**单一职责原则**，按业务域划分微服务：

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                 │
│  CTMS Web  │  EDC Web  │  IWRS Web  │  医生病历夹 Web  │  Admin  │
└─────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────────┐
│                      API 网关 (Kong/APISIX)                       │
│  • 路由分发  • 身份验证  • 限流熔断  • 审计日志  • API 版本管理    │
└─────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌─────▼────────┐ ┌─────▼──────────┐
│  CTMS 服务群    │ │  EDC 服务群   │ │  IWRS 服务群    │
│ • 项目管理服务  │ │ • eCRF 服务   │ │ • 随机化服务   │
│ • 中心管理服务  │ │ • 数据录入服务│ │ • 药物管理服务 │
│ • 供应商服务    │ │ • 核查服务   │ │ • 揭盲服务     │
│ • 工时服务      │ │ • SDTM 导出服务│ │ • 供应服务     │
│ • eTMF 服务     │ │ • SAE 服务    │ │               │
└────────────────┘ └─────────────┘ └─────────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
┌─────────────────────────────────────────────────────────────────┐
│                      共享服务层                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 认证服务  │ │ 审计追踪  │ │ 电子签名  │ │ 通知服务  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 文件存储  │ │ 工作流引擎│ │ 报表引擎  │ │ 规则引擎  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────────┐
│                      数据层                                      │
│  PostgreSQL (主) │ Redis (缓存) │ RabbitMQ (消息) │ MinIO (文件) │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 服务列表

| 服务名 | 端口 | 职责 | 数据库 |
|--------|------|------|--------|
| **gateway-service** | 3000 | API 网关，路由分发 | - |
| **auth-service** | 3001 | 用户认证、权限管理、SSO | auth_db |
| **ctms-project-service** | 3010 | 项目管理、中心管理 | ctms_db |
| **ctms-timesheet-service** | 3011 | 工时填报、审批 | ctms_db |
| **ctms-etmf-service** | 3012 | 文档管理、电子签名 | ctms_db + MinIO |
| **edc-template-service** | 3020 | eCRF 模板设计、版本管理 | edc_db |
| **edc-data-service** | 3021 | 数据录入、查询管理 | edc_db |
| **edc-validation-service** | 3022 | 数据核查规则引擎 | edc_db |
| **edc-sdtm-service** | 3023 | SDTM 数据转换、导出 | edc_db |
| **iwrs-randomization-service** | 3030 | 随机化算法、揭盲 | iwrs_db |
| **iwrs-supply-service** | 3031 | 药物库存、发货 | iwrs_db |
| **portfolio-service** | 3040 | 医生病历夹、患者管理 | portfolio_db |
| **audit-service** | 3050 | 审计追踪（所有服务调用） | audit_db |
| **notification-service** | 3051 | 邮件、短信、站内信 | - |
| **workflow-service** | 3052 | 审批流引擎 | workflow_db |

---

## 2. 通信机制

### 2.1 同步通信（REST API）

**场景**：需要即时响应的操作

```typescript
// 示例：EDC 数据服务调用审计服务
// POST /api/v1/audit/logs
{
  "system": "edc",
  "module": "crf_data",
  "action": "create",
  "userId": "user_123",
  "recordId": "crf_456",
  "details": { /* ... */ }
}
```

### 2.2 异步通信（RabbitMQ）

**场景**：跨服务业务、批量处理、解耦

```typescript
// 消息队列定义
interface ExchangeConfig {
  name: string;
  type: 'direct' | 'topic' | 'fanout';
}

// 核心队列
const queues = {
  // EDC 相关
  'edc.data.validated': { exchange: 'edc.events', routingKey: 'data.validated' },
  'edc.query.created': { exchange: 'edc.events', routingKey: 'query.created' },
  
  // 审计相关
  'audit.log.async': { exchange: 'audit.events', routingKey: 'log.*' },
  
  // 通知相关
  'notification.email': { exchange: 'notification.events', routingKey: 'email' },
  'notification.sms': { exchange: 'notification.events', routingKey: 'sms' },
  
  // SDTM 导出
  'sdtm.export.started': { exchange: 'sdtm.events', routingKey: 'export.started' },
  'sdtm.export.completed': { exchange: 'sdtm.events', routingKey: 'export.completed' },
};
```

### 2.3 服务间调用示例

```typescript
// EDC 数据录入 → 触发核查 → 发送通知 → 记录审计
async function saveCrfData(data: CrfDataInput) {
  // 1. 保存数据
  const savedData = await edcDataService.create(data);
  
  // 2. 异步触发核查（发送消息到队列）
  await rabbitMQ.publish('edc.data.validated', {
    crfDataId: savedData.id,
    subjectId: data.subjectId,
  });
  
  // 3. 异步记录审计
  await rabbitMQ.publish('audit.log.async', {
    system: 'edc',
    action: 'create',
    recordType: 'CrfData',
    recordId: savedData.id,
    userId: data.changedBy,
  });
  
  return savedData;
}
```

---

## 3. 数据模型设计（Prisma Schema）

### 3.1 用户与认证（auth_service）

```prisma
// schema/auth/prisma/schema.prisma

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

// 租户（多租户基础）
model Tenant {
  id           String   @id @default(uuid())
  name         String
  code         String   @unique  // 租户编码（用于 URL 路由）
  type         TenantType
  dbIsolation  DbIsolationType @default(logical)  // 物理隔离或逻辑隔离
  status       TenantStatus   @default(active)
  config       JsonMap  // 租户配置（功能开关、自定义配置）
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
  
  users        User[]
  trials       ClinicalTrial[]  // 该租户的试验
  
  @@map("tenants")
}

enum TenantType {
  enterprise  // 大客户（独立数据库）
  smb         // 中小客户（逻辑隔离）
}

enum DbIsolationType {
  physical  // 独立数据库
  logical   // tenant_id 隔离
}

enum TenantStatus {
  active
  suspended
  expired
}

// 用户
model User {
  id              String   @id @default(uuid())
  tenantId        String   @map("tenant_id")
  email           String   @unique
  passwordHash    String   @map("password_hash")
  name            String
  phone           String?
  avatar          String?
  status          UserStatus @default(active)
  mfaEnabled      Boolean  @default(false) @map("mfa_enabled")
  lastLoginAt     DateTime? @map("last_login_at")
  systemAccess    JsonMap  @map("system_access")  // { ctms: true, edc: false, ... }
  roles           UserRole[]
  auditLogs       AuditLog[]
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  
  @@index([tenantId], map: "idx_user_tenant")
  @@map("users")
}

enum UserStatus {
  active
  inactive
  locked
  deleted
}

// 用户角色（多系统、多角色）
model UserRole {
  id         String   @id @default(uuid())
  userId     String   @map("user_id")
  system     SystemType
  roleName   String   @map("role_name")  // 如 "Data Manager"
  permissions JsonMap  // ["edc.crf.edit", "edc.crf.lock", ...]
  createdAt  DateTime @default(now())
  
  user User @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  @@unique([userId, system, roleName], map: "uk_user_system_role")
  @@map("user_roles")
}

enum SystemType {
  ctms
  edc
  iwrs
  portfolio
  admin
}

// 会话管理（用于多设备登录控制）
model Session {
  id         String   @id @default(uuid())
  userId     String   @map("user_id")
  deviceId   String   @map("device_id")  // 设备指纹
  ipAddress  String   @map("ip_address")
  userAgent  String   @map("user_agent")
  expiresAt  DateTime @map("expires_at")
  createdAt  DateTime @default(now())
  
  user User @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  @@index([userId], map: "idx_session_user")
  @@map("sessions")
}
```

### 3.2 CTMS 核心模型

```prisma
// schema/ctms/prisma/schema.prisma

// 临床试验（项目）
model ClinicalTrial {
  id              String   @id @default(uuid())
  tenantId        String   @map("tenant_id")
  protocolNumber  String   @unique @map("protocol_number")
  title           String
  shortTitle      String?  @map("short_title")
  phase           TrialPhase
  status          TrialStatus @default(protocol_development)
  theraticArea    String?  @map("therapeutic_area")  // 治疗领域
  startDate       DateTime?
  endDate         DateTime?
  budget          Decimal  @db.Decimal(18, 2)
  currency        String   @default("CNY")
  
  sites           Site[]
  documents       TMFDocument[]
  timesheets      Timesheet[]
  edcTemplates    EdcTemplate[]
  randomizations  Randomization[]
  
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  
  @@index([tenantId], map: "idx_trial_tenant")
  @@map("clinical_trials")
}

enum TrialPhase {
  phase_i  = "I"
  phase_ii = "II"
  phase_iii = "III"
  phase_iv = "IV"
}

enum TrialStatus {
  protocol_development = "Protocol Development"
  startup = "Startup"
  recruitment = "Recruitment"
  ongoing = "Ongoing"
  data_clean = "Data Clean"
  locked = "Locked"
  completed = "Completed"
  terminated = "Terminated"
}

// 研究中心
model Site {
  id             String   @id @default(uuid())
  trialId        String   @map("trial_id")
  siteNumber     String   @map("site_number")  // 中心编号（如 1001）
  name           String   // 机构名称
  address        String?
  piName         String   @map("pi_name")  // 主要研究者
  piEmail        String?  @map("pi_email")
  piPhone        String?  @map("pi_phone")
  status         SiteStatus @default(identification)
  activationDate DateTime? @map("activation_date")
  deactivateDate DateTime? @map("deactivate_date")
  
  trial ClinicalTrial @relation(fields: [trialId], references: [id])
  subjects Subject[]
  
  @@unique([trialId, siteNumber], map: "uk_trial_site")
  @@map("sites")
}

enum SiteStatus {
  identification = "Identification"
  selection = "Selection"
  activation预备 = "Activation Prep"
  active = "Active"
  onHold = "On Hold"
  completed = "Completed"
  closed = "Closed"
}

// eTMF 文档
model TMFDocument {
  id          String   @id @default(uuid())
  trialId     String   @map("trial_id")
  category    String   // TMF 分类（A 总体试验文档）
  subcategory String   // 子分类（A1 方案）
  filename    String
  version     Int      @default(1)
  filesize    Int?     @map("file_size")
  fileUrl     String   @map("file_url")  // MinIO/S3 路径
  mimeTyp     String?  @map("mime_type")
  signed      Boolean  @default(false)
  signerId    String?  @map("signer_id")
  signDate    DateTime? @map("sign_date")
  status      DocumentStatus @default(draft)
  
  trial ClinicalTrial @relation(fields: [trialId], references: [id])
  signatures ElectronicSignature[]
  auditLogs  AuditLog[]
  
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  @@index([trialId], map: "idx_doc_trial")
  @@index([category, subcategory], map: "idx_doc_category")
  @@map("tmf_documents")
}

enum DocumentStatus {
  draft = "Draft"
  review = "In Review"
  approved = "Approved"
  archived = "Archived"
}

// 工时记录
model Timesheet {
  id          String   @id @default(uuid())
  userId      String   @map("user_id")
  trialId     String?  @map("trial_id")  // 可关联具体项目
  date        DateTime  // 工作日期
  hours       Decimal  @db.Decimal(4, 2)  // 工时（小时）
  taskType    String   @map("task_type")  // 任务类型
  description String?
  billable    Boolean  @default(true)  // 是否可计费
  status      TimesheetStatus @default(draft)
  approverId  String?  @map("approver_id")
  approvedAt  DateTime? @map("approved_at")
  
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  @@index([userId], map: "idx_timesheet_user")
  @@index([trialId], map: "idx_timesheet_trial")
  @@index([date], map: "idx_timesheet_date")
  @@map("timesheets")
}

enum TimesheetStatus {
  draft = "Draft"
  submitted = "Submitted"
  approved = "Approved"
  rejected = "Rejected"
}
```

### 3.3 EDC 核心模型

```prisma
// schema/edc/prisma/schema.prisma

// EDC 模板（对应一个 Trial 的 eCRF 设计）
model EdcTemplate {
  id           String   @id @default(uuid())
  trialId      String   @unique @map("trial_id")
  name         String
  version      String   @default("1.0")
  status       TemplateStatus @default(draft)
  cdashVersion String   @default("4.0") @map("cdash_version")
  sdtmVersion  String   @default("3.3") @map("sdtm_version")
  pages        JsonMap  // 页面结构（序列化存储）
  metadata     JsonMap  // 模板元数据（创建人、语言等）
  
  subjects     Subject[]  // 使用该模板的受试者
  
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
  
  @@map("edc_templates")
}

enum TemplateStatus {
  draft = "Draft"
  inReview = "In Review"
  active = "Active"
  deprecated = "Deprecated"
}

// 受试者
model Subject {
  id             String   @id @default(uuid())
  trialId        String   @map("trial_id")
  siteId         String   @map("site_id")
  subjectNumber  String   @map("subject_number")  // 受试者编号
  status         SubjectStatus @default(screened)
  enrollmentDate DateTime? @map("enrollment_date")
  completionDate DateTime? @map("completion_date")
  withdrawReason String?  @map("withdraw_reason")
  
  template EdcTemplate @relation(fields: [trialId], references: [id])
  site Site @relation(fields: [siteId], references: [id])
  crfData  CrfData[]
  queries  Query[]
  
  @@unique([trialId, subjectNumber], map: "uk_trial_subject")
  @@index([siteId], map: "idx_subject_site")
  @@map("subjects")
}

enum SubjectStatus {
  screened = "Screened"
  enrolled = "Enrolled"
  ongoing = "Ongoing"
  completed = "Completed"
  withdrawn = "Withdrawn"
  lostToFollowUp = "Lost to Follow-up"
}

// CRF 数据（EAV 模型：Entity-Attribute-Value）
model CrfData {
  id          String   @id @default(uuid())
  subjectId   String   @map("subject_id")
  pageId      String   @map("page_id")  // eCRF 页面 ID
  sectionId   String?  @map("section_id")  // 区块 ID（可重复区块）
  fieldName   String   @map("field_name")  // 字段名（英文变量名）
  fieldValue  String?  @map("field_value")  // 值（统一用 JSON 字符串）
  numericValue Decimal? @map("numeric_value")  // 数值类型（用于排序、统计）
  dateValue    DateTime? @map("date_value")  // 日期类型
  
  oldValue     String?  @map("old_value")  // 审计追踪（旧值）
  changedBy    String   @map("changed_by")  // 修改人 ID
  changedAt    DateTime @default(now()) @map("changed_at")
  reason       String?  // 修改原因
  
  queryStatus  String?  @map("query_status")  // 如有未解决查询
  
  subject Subject @relation(fields: [subjectId], references: [id], onDelete: Cascade)
  
  @@index([subjectId], map: "idx_crf_subject")
  @@index([pageId], map: "idx_crf_page")
  @@index([fieldName], map: "idx_crf_field")
  @@map("crf_data")
}

// 数据核查（Query）
model Query {
  id            String   @id @default(uuid())
  subjectId     String   @map("subject_id")
  crfDataId     String?  @map("crf_data_id")  // 关联具体字段（可为空，如页面级查询）
  ruleId        String?  @map("rule_id")  // 触发的核查规则 ID
  ruleName      String?  @map("rule_name")
  queryType     QueryType
  severity      QuerySeverity
  message       String   // 核查信息
  status        QueryStatus @default(open)
  
  createdBy     String   @map("created_by")
  createdAt     DateTime @default(now())
  
  resolvedBy    String?  @map("resolved_by")
  resolvedAt    DateTime? @map("resolved_at")
  resolutionComment String? @map("resolution_comment")
  
  subject Subject @relation(fields: [subjectId], references: [id], onDelete: Cascade)
  
  @@index([subjectId], map: "idx_query_subject")
  @@index([status], map: "idx_query_status")
  @@map("queries")
}

enum QueryType {
  automatic = "Automatic"  // 系统自动触发
  manual = "Manual"        // 人工创建
}

enum QuerySeverity {
  info = "Info"
  warning = "Warning"
  error = "Error"
  critical = "Critical"
}

enum QueryStatus {
  open = "Open"
  answering = "Answering"
  answered = "Answered"
  reviewing = "Reviewing"
  resolved = "Resolved"
  reopened = "Reopened"
  closed = "Closed"
}

// 核查规则定义
model ValidationRule {
  id          String   @id @default(uuid())
  templateId  String   @map("template_id")
  name        String
  description String?
  ruleType    RuleType
  targetType  TargetType  // 字段级、页面级、跨页面
  targetId    String?     // 目标字段/页面 ID
  expression  String      // 规则表达式（JavaScript）
  message     String      // 触发时的提示消息
  severity    QuerySeverity
  enabled     Boolean    @default(true)
  
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  @@index([templateId], map: "idx_rule_template")
  @@map("validation_rules")
}

enum RuleType {
  required = "Required"          // 必填
  data_type = "Data Type"        // 数据类型
  range = "Range"                // 取值范围
  date_logic = "Date Logic"      // 日期逻辑
  cross_field = "Cross Field"    // 跨字段
  custom = "Custom"              // 自定义表达式
}

enum TargetType {
  field = "Field"
  section = "Section"
  page = "Page"
  cross_page = "Cross Page"
}
```

### 3.4 IWRS 核心模型

```prisma
// schema/iwrs/prisma/schema.prisma

// 随机化记录
model Randomization {
  id                String   @id @default(uuid())
  trialId           String   @map("trial_id")
  subjectId         String   @map("subject_id")
  siteId            String   @map("site_id")
  strataKey         String   @map("strata_key")  // 分层键（如"1001_mild"）
  treatmentGroup    String   @map("treatment_group")
  kitNumber         String   @map("kit_number")  // 药物包装号
  randomizationNumber Int    @map("randomization_number")
  blockId           String?  @map("block_id")  // 区组 ID
  positionInBlock   Int?     @map("position_in_block")
  
  randomizedBy     String   @map("randomized_by")
  randomizedAt     DateTime @default(now()) @map("randomized_at")
  
  unblinding      EmergencyUnblinding?  // 应急揭盲记录
  
  @@unique([trialId, subjectId], map: "uk_trial_subject")
  @@index([siteId], map: "idx_randomization_site")
  @@index([strataKey], map: "idx_randomization_strata")
  @@map("randomizations")
}

// 随机化列表（预生成的区组模式）
model RandomizationList {
  id            String   @id @default(uuid())
  trialId       String   @map("trial_id")
  strataKey     String   @map("strata_key")
  blockSize     Int      @map("block_size")
  blockPattern  JsonMap  // 区组模式（如 ["A", "B", "P", "A", "B", "P"]）
  currentPosition Int    @default(0) @map("current_position")
  status        ListStatus @default(active)
  
  createdAt     DateTime @default(now())
  
  @@unique([trialId, strataKey], map: "uk_trial_strata")
  @@map("randomization_lists")
}

enum ListStatus {
  active = "Active"
  completed = "Completed"
  locked = "Locked"
}

// 应急揭盲
model EmergencyUnblinding {
  id                 String   @id @default(uuid())
  randomizationId    String   @unique @map("randomization_id")
  reason             String   // 揭盲原因（必填）
  unblindedBy        String   @map("unblinded_by")
  unblindedAt        DateTime @default(now()) @map("unblinded_at")
  treatmentRevealed  String   @map("treatment_revealed")
  isMedicalEmergency Boolean  @default(true) @map("is_medical_emergency")
  
  randomization Randomization @relation(fields: [randomizationId], references: [id], onDelete: Cascade)
  
  @@map("emergency_unblinding")
}

// 药物库存
model DrugInventory {
  id           String   @id @default(uuid())
  trialId      String   @map("trial_id")
  siteId       String   @map("site_id")
  kitNumber    String   @map("kit_number")
  treatmentGroup String? @map("treatment_group")  // 如已揭盲
  quantity     Int
  unit         String   // 包装单位（盒、瓶）
  status       InventoryStatus @default(inWarehouse)
  expirationDate DateTime? @map("expiration_date")
  
  allocatedTo  String?  @map("allocated_to")  // 分配给哪个受试者
  allocatedAt  DateTime? @map("allocated_at")
  returnedAt   DateTime? @map("returned_at")
  
  @@unique([trialId, kitNumber], map: "uk_trial_kit")
  @@index([siteId], map: "idx_inventory_site")
  @@map("drug_inventory")
}

enum InventoryStatus {
  inWarehouse = "In Warehouse"
  shipped = "Shipped"
  received = "Received"
  allocated = "Allocated"
  returned = "Returned"
  used = "Used"
  discontinued = "Discontinued"
}
```

### 3.5 审计追踪（共享服务）

```prisma
// schema/audit/prisma/schema.prisma

model AuditLog {
  id         String   @id @default(uuid())
  tenantId   String   @map("tenant_id")
  system     SystemType
  module     String   // 模块（如"eCRF"）
  recordType String   @map("record_type")  // 记录类型（如"CrfData"）
  recordId   String   @map("record_id")
  action     AuditAction
  userId     String?  @map("user_id")
  userName   String?  @map("user_name")
  oldValue   JsonMap? @map("old_value")
  newValue   JsonMap? @map("new_value")
  reason     String?
  ipAddress  String?  @map("ip_address")
  userAgent  String?  @map("user_agent")
  timestamp  DateTime @default(now())
  
  @@index([tenantId], map: "idx_audit_tenant")
  @@index([system], map: "idx_audit_system")
  @@index([recordType, recordId], map: "idx_audit_record")
  @@index([timestamp], map: "idx_audit_time")
  @@map("audit_logs")
}

enum AuditAction {
  create
  update
  delete
  sign
  unlock
  export
  login
  logout
  permission_change
}
```

---

## 4. API 设计规范

### 4.1 RESTful 约定

```
GET     /api/v1/{resource}          # 列表（支持分页、过滤、排序）
GET     /api/v1/{resource}/{id}     # 详情
POST    /api/v1/{resource}          # 创建
PUT     /api/v1/{resource}/{id}     # 全量更新
PATCH   /api/v1/{resource}/{id}     # 部分更新
DELETE  /api/v1/{resource}/{id}     # 删除
```

### 4.2 统一响应格式

```typescript
// 成功响应
{
  "code": 0,
  "message": "success",
  "data": { /* ... */ },
  "requestId": "req_123456"  // 用于追踪
}

// 错误响应
{
  "code": 400101,
  "message": "参数验证失败",
  "data": null,
  "requestId": "req_123456"
}

// 分页响应
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [/* ... */],
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "totalPages": 5
  }
}
```

### 4.3 核心 API 示例

#### EDC API

```typescript
// 创建 eCRF 模板
POST /api/v1/edc/templates
{
  "trialId": "trial_123",
  "name": "肿瘤临床试验 eCRF",
  "pages": [/* 页面结构 */]
}

// 获取受试者 CRF 数据
GET /api/v1/edc/subjects/{subjectId}/crf-data?pageId=page_456

// 保存 CRF 数据
POST /api/v1/edc/crf-data
{
  "subjectId": "sub_789",
  "pageId": "page_456",
  "sectionId": "section_1",
  "field_name": "AESER",
  "field_value": "Y",
  "changed_by": "user_123"
}

// 查询管理
GET  /api/v1/edc/queries?subjectId=sub_789&status=open
POST /api/v1/edc/queries/resolve
{
  "queryId": "query_456",
  "resolutionComment": "数据已确认，核查关闭",
  "resolvedBy": "user_789"
}
```

#### IWRS API

```typescript
// 受试者随机化
POST /api/v1/iwrs/randomize
{
  "trialId": "trial_123",
  "subjectId": "sub_456",
  "siteId": "site_789",
  "strata": {
    "severity": "mild"
  },
  "randomizedBy": "user_123"
}

// 应急揭盲
POST /api/v1/iwrs/unblind
{
  "randomizationId": "rand_789",
  "reason": "医疗紧急情况",
  "unblindedBy": "user_456"
}
```

#### CTMS API

```typescript
// 创建项目
POST /api/v1/ctms/trials
{
  "protocolNumber": "CT-2026-001",
  "title": "某药物临床试验",
  "phase": "III",
  "budget": 10000000
}

// 工时填报
POST /api/v1/ctms/timesheets
{
  "trialId": "trial_123",
  "date": "2026-05-27",
  "hours": 8,
  "taskType": "数据管理",
  "description": "完成 CRF 数据核查"
}
```

---

## 5. 部署架构

### 5.1 Kubernetes 部署

```yaml
# k8s/edc-data-service/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: edc-data-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: edc-data-service
  template:
    metadata:
      labels:
        app: edc-data-service
    spec:
      containers:
      - name: edc-data-service
        image: clinical-trials/edc-data-service:v1.0.0
        ports:
        - containerPort: 3021
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: edc-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3021
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: edc-data-service
spec:
  selector:
    app: edc-data-service
  ports:
  - port: 3021
    targetPort: 3021
  type: ClusterIP
```

### 5.2 数据库主从架构

```
┌─────────────────┐
│   Primary DB    │  ← 写操作
│   (主库)         │
└────────┬────────┘
         │ 异步复制
         ▼
   ┌──────────────┐
   │  Read Replica 1 │  ← 读操作（负载均衡）
   └──────────────┘
         │
   ┌──────────────┘
   │  Read Replica 2 │  ← 读操作（负载均衡）
   └───────────────┘
```

---

## 6. 安全设计

### 6.1 认证与授权

- **OAuth 2.0 + JWT**：无状态认证，微服务间传递用户上下文
- **RBAC**：基于角色的权限控制，细粒度到 API 级别
- **多因素认证（MFA）**：支持 TOTP、短信验证码

### 6.2 数据安全

- **传输加密**：TLS 1.3（所有服务间通信）
- **存储加密**：AES-256（敏感字段：患者姓名、身份证号）
- **数据脱敏**：导出时自动脱敏（姓名→编号）

### 6.3 审计合规

- **不可篡改**：审计日志只读，任何修改需记录新日志
- **保留周期**：至少 7 年（符合 FDA 要求）
- **定期备份**：每日增量，每周全量

---

## 文档结束

**下一步**：
1. 评审此架构设计，确认服务拆分和数据库模型
2. 开始生成 Prisma schema 文件
3. 搭建基础项目框架（Monorepo 结构）
