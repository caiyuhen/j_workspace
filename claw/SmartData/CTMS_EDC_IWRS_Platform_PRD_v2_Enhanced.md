# CTMS_EDC_IWRS 平台开发文档增强版

## 1. 文档核心功能模块

### 1.1 CTMS模块（临床试验管理）

#### 1.1.1 试验项目管理
- **功能描述**：管理临床试验的全生命周期，从方案启动到数据锁库。
- **关键字段**：试验编号、名称、方案版本、试验类型、赞助商、主要研究者、伦理委员会、试验状态
- **用户故事**：
  - 项目经理创建试验项目并配置基本信息
  - 研究者查看试验的入组进度和数据录入状态
  - 监查员收到试验关键节点的提醒

#### 1.1.2 工时管理系统
- **功能描述**：记录和管理项目成员的工时投入，支持项目成本核算
- **核心数据结构**：
  ```typescript
  interface WorkHour {
    id: string;
    projectId: string;
    userId: string;
    date: Date;
    hours: number;
    workType: string;
    description: string;
    status: 'pending' | 'approved' | 'rejected';
  }
  ```
- **关键字段**：工时类型（数据录入、质疑回复、监查访视等）、审批流程、成本计算

#### 1.1.3 eTMF 电子试验主文件
- **功能描述**：管理临床试验文档，支持在线编辑、版本控制、审批流程
- **核心功能**：
  - 符合 TMF Reference Model 2.0 的文件夹结构
  - 支持格式：PDF、DOCX、XLSX、PPTX、图片、压缩包
  - 全文检索（Elasticsearch）
  - 审计追踪记录

### 1.2 EDC模块（电子数据采集）

#### 1.2.1 拖拉拽式 eCRF 设计器
- **功能描述**：可视化设计 eCRF 表单，自动匹配 CDASH 标准字段
- **CDASH 标准字段库**：
  ```typescript
  interface CDASH_Field {
    variableName: string;
    displayLabel: string;
    domain: string;
    fieldType: FieldType;
    allowedValues?: string[];
    validationPattern?: string;
    sdtmMapping?: {
      domain: string;
      variable: string;
    };
  }
  ```
- **验证规则**：合理性检查、范围检查、跨页核查、内部一致性

#### 1.2.2 数据采集与录入
- **功能描述**：支持多用户并发录入患者数据，实时数据核查与质疑管理
- **核心数据结构**：
  ```typescript
  interface CrfData {
    id: string;
    crfFormId: string;
    patientId: string;
    visitNumber: number;
    data: Record<string, any>;
    status: 'draft' | 'submitted' | 'approved';
    createdAt: Date;
    updatedAt: Date;
  }
  
  interface Query {
    id: string;
    crfDataId: string;
    field: string;
    text: string;
    status: 'new' | 'replied' | 'closed' | 'rejected';
    priority: 'high' | 'medium' | 'low';
    createdAt: Date;
    repliedAt?: Date;
  }
  ```

#### 1.2.3 SDTM 数据映射与导出
- **功能描述**：将 eCRF 数据自动映射到 SDTM 标准格式
- **核心数据结构**：
  ```typescript
  interface SDTM_Mapping {
    sourceField: string;
    targetDomain: string;
    targetVariable: string;
    transformRule?: string;
  }
  ```

### 1.3 IWRS模块（交互式随机化与药物供应管理）

#### 1.3.1 随机化管理
- **功能描述**：配置随机化算法，管理患者随机化与破盲流程
- **核心数据结构**：
  ```typescript
  interface RandomizationConfig {
    algorithm: 'SIMPLE' | 'BLOCK' | 'STRATIFIED' | 'DYNAMIC';
    treatmentArms: TreatmentArm[];
    blockSizes?: number[];
    stratificationFactors?: string[];
    allocationRatio: number[];
  }
  
  interface PatientRandomization {
    id: string;
    patientId: string;
    trialId: string;
    treatmentArm: string;
    randomizationDate: Date;
    randomizationCode: string;
    createdBy: string;
  }
  ```

#### 1.3.2 药物供应管理
- **功能描述**：管理研究药物的库存、分发、回收与报废
- **核心数据结构**：
  ```typescript
  interface DrugBatch {
    id: string;
    drugName: string;
    specification: string;
    batchNumber: string;
    expirationDate: Date;
    quantity: number;
    unit: string;
    storageLocation: string;
  }
  ```

### 1.4 医生个人病历夹模块

#### 1.4.1 患者管理
- **功能描述**：医生管理个人患者档案，支持随访数据录入与长期追踪
- **核心数据结构**：
  ```typescript
  interface Patient {
    id: string;
    name: string;
    gender: 'male' | 'female' | 'other';
    dateOfBirth: Date;
    contactInfo: string;
    diagnosis: string;
    treatmentHistory: string[];
    patientTags: string[];
  }
  ```

#### 1.4.2 自定义表单设计
- **功能描述**：拖拉拽设计随访数据收集表单，可引用 EDC 已有模板

### 1.5 安全管理中心（新增）

#### 1.5.1 审计追踪
- **功能描述**：全面记录系统关键操作，符合监管要求
- **核心数据结构**：
  ```typescript
  interface AuditRecord {
    eventId: string;
    eventType: string;
    timestamp: string;
    userId: string;
    userName: string;
    ipAddress: string;
    userAgent: string;
    module: string;
    entity: string;
    entityId: string;
    oldValue?: string;
    newValue?: string;
    reason?: string;
  }
  ```

#### 1.5.2 数据加密与脱敏
- **功能描述**：保护敏感数据安全，防止数据泄露
- **加密方式**：AES-256、国密 SM4（支持字段级加密）

### 1.6 系统集成模块

#### 1.6.1 外部系统接口
- **功能描述**：与 EHR、LIS、PACS 等外部医疗系统集成
- **支持协议**：HL7 v2.x、FHIR R4
- **核心接口**：
  - 患者信息同步接口
  - 实验室检验结果接口
  - 表格数据导入/导出接口

## 2. 技术实现细节

### 2.1 数据模型要求

#### 2.1.1 EDC相关数据模型
1. **EdcTemplate** - eCRF模板
   ```sql
   CREATE TABLE edc_templates (
     id UUID PRIMARY KEY,
     name VARCHAR(255),
     description TEXT,
     fields JSONB,
     created_by UUID,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. **CrfForm** - CRF表单定义
   ```sql
   CREATE TABLE crf_forms (
     id UUID PRIMARY KEY,
     template_id UUID REFERENCES edc_templates(id),
     study_id UUID,
     name VARCHAR(255),
     version VARCHAR(50),
     status VARCHAR(50),
     created_by UUID,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **CrfFormField** - CRF字段定义
   ```sql
   CREATE TABLE crf_form_fields (
     id UUID PRIMARY KEY,
     form_id UUID REFERENCES crf_forms(id),
     field_name VARCHAR(255),
     label VARCHAR(255),
     field_type VARCHAR(50),
     required BOOLEAN DEFAULT FALSE,
     validation_rules JSONB
   );
   ```

4. **CrfData** - 数据录入内容
   ```sql
   CREATE TABLE crf_data (
     id UUID PRIMARY KEY,
     form_id UUID REFERENCES crf_forms(id),
     patient_id UUID,
     visit_number INTEGER,
     data JSONB,
     status VARCHAR(50),
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

5. **AdverseEvent** - 不良事件管理
   ```sql
   CREATE TABLE adverse_events (
     id UUID PRIMARY KEY,
     patient_id UUID,
     study_id UUID,
     event_date DATE,
     event_description TEXT,
     seriousness VARCHAR(50),
     outcome VARCHAR(50),
     causality VARCHAR(50),
     created_by UUID,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

#### 2.1.2 用户权限和审计数据模型
```sql
-- 用户权限表
CREATE TABLE user_permissions (
  user_id UUID,
  role VARCHAR(50),
  resource_type VARCHAR(100),
  resource_id UUID,
  permissions JSONB,
  PRIMARY KEY (user_id, role, resource_type, resource_id)
);

-- 审计追踪记录
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  event_type VARCHAR(100),
  user_id UUID,
  ip_address VARCHAR(50),
  user_agent TEXT,
  resource_type VARCHAR(100),
  resource_id UUID,
  old_value JSONB,
  new_value JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 接口规范

#### 2.2.1 REST API设计要求
- **资源命名**：使用名词复数形式
- **状态码**：遵循HTTP状态码标准
- **错误处理**：统一的JSON错误响应格式
- **版本控制**：URL中包含API版本号（如：/api/v1/）

示例：
```http
GET /api/v1/crf-forms/:id
GET /api/v1/crf-data?studyId=uuid&patientId=uuid
POST /api/v1/adverse-events
PUT /api/v1/crf-data/:id
```

#### 2.2.2 数据格式规范
- **请求体**：JSON格式
- **响应体**：统一的API响应格式
- **时间格式**：ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)
- **数据校验**：使用Zod进行端到端验证

```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}
```

### 2.3 数据库设计
- **数据库选型**：PostgreSQL (符合CDISC标准)
- **存储引擎**：JSONB字段支持灵活数据结构
- **索引策略**：关键查询字段建立复合索引
- **分片策略**：按tenant_id进行水平分片

```sql
-- 建议索引
CREATE INDEX idx_crf_data_patient_visit ON crf_data(patient_id, visit_number);
CREATE INDEX idx_adverse_events_patient ON adverse_events(patient_id);
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, created_at);
```

### 2.4 安全要求
- **认证授权**：JWT + OAuth2.0 + RBAC
- **数据加密**：
  - TLS 1.3加密传输
  - AES-256/SM4字段级存储加密
  - 密钥管理使用HSM或云KMS
- **安全审计**：
  - 审计日志不可篡改
  - 异常行为自动检测与告警
  - 审计日志90天以上保留

## 3. 开发规范

### 3.1 代码风格指南
#### 3.1.1 TypeScript/JavaScript 规范
- 使用Prettier进行代码格式化
- ESLint + TypeScript ESLint
- 统一的命名约定（PascalCase类名，camelCase变量名）
- 严格类型定义，接口统一管理

#### 3.1.2 模块结构
```
src/
├── dto/           # 数据传输对象
├── service/       # 业务逻辑服务
├── controller/    # 控制器层
├── routes/        # 路由定义
├── middleware/    # 中间件定义
├── util/          # 工具类函数
└── config/        # 配置文件
```

#### 3.1.3 Zod验证策略
```typescript
import { z } from 'zod';

// 用户创建表单验证
const userCreateSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(['admin', 'researcher', 'crc'])
});

export type UserCreateDto = z.infer<typeof userCreateSchema>;
```

### 3.2 前端组件要求
#### 3.2.1 React Component结构
- 使用函数式组件 + hooks
- 组件按功能模块划分
- 统一的UI组件库使用Ant Design
- 动态导入和代码分割优化加载性能

#### 3.2.2 状态管理
- 使用Zustand进行轻量级全局状态管理
- 按页面或功能模块组织状态
- 状态持久化支持（localStorage/sessionStorage）

### 3.3 后端业务逻辑要求
#### 3.3.1 服务层结构
```typescript
// 示例：CRF数据服务
class CrfDataService {
  async createCrfData(data: CrfDataInput) {
    // 数据验证
    const validatedData = this.validateCrfData(data);
    
    // 数据存储 
    const crfData = await this.crfDataRepository.create(validatedData);
    
    // 审计日志
    await this.auditService.logCreate('crf_data', crfData.id, data);
    
    return crfData;
  }
  
  async validateCrfData(data: any): Promise<CrfData> {
    // 数据验证逻辑
    return data;
  }
}
```

#### 3.3.2 路由设计
```typescript
// 示例：CRF数据路由
const crfRoutes = [
  { method: 'GET', path: '/crf-data/:id', handler: getSingleCrfData },
  { method: 'GET', path: '/crf-data', handler: getCrfDataList },
  { method: 'POST', path: '/crf-data', handler: createCrfData },
  { method: 'PUT', path: '/crf-data/:id', handler: updateCrfData },
  { method: 'DELETE', path: '/crf-data/:id', handler: deleteCrfData }
];
```

## 4. 特殊需求

### 4.1 CDISC标准合规性
#### 4.1.1 eCRF与SDTM标准适配
- **CDASH标准字段库**：包含超过500个标准字段
- **字段映射管理**：图形化配置CDASH到SDTM的映射关系
- **数据导出规范**：支持CSV、JSON、SAS xpt等标准格式

#### 4.1.2 实施要求
- eCRF字段命名遵守CDASH规范
- SDTM映射配置可维护
- 导出数据通过CDISC验证工具(DVS)验证
- Define.xml文档自动生成

### 4.2 导出功能
#### 4.2.1 6类CSV/JSON导出
1. **患者数据**：人口学、入组、退出信息
2. **访视数据**：各访视数据收集
3. **实验室数据**：检查结果、生命体征
4. **安全性数据**：不良事件、严重不良事件
5. **用药数据**：药物使用记录
6. **分析数据**：用于统计分析的数据集

#### 4.2.2 导出格式规范
- **CSV**：UTF-8编码，CSV格式
- **JSON**：结构化JSON数据
- **SAS xpt**：CDISC标准格式

### 4.3 GCP合规要求
#### 4.3.1 21 CFR Part 11规范实现
- **电子记录与签名**：满足FDA要求
- **完整性要求**：审计追踪完整记录
- **系统验证**：验证文档齐全
- **访问控制**：基于角色的权限管理

#### 4.3.2 临床数据保护
- **数据分类**：患者身份信息、临床数据分级保护
- **权限管控**：最小权限原则
- **数据脱敏**：导出数据需要自动脱敏
- **跨境传输**：符合GDPR要求的数据跨境传输

## 5. 项目实施建议

### 5.1 开发优先级建议

要求EDC、CTMS、IWRS、医生病历夹使不同的登录页面，同时生成一个统一的登录界面

1. **第一阶段**：EDC核心模块（表单设计器、数据录入、核查规则）
2. **第二阶段**：CTMS模块（项目管理、工时系统、eTMF）
3. **第三阶段**：IWRS模块（随机化、药品供应）
4. **第四阶段**：安全模块（审计、加密、合规）
5. **第五阶段**：集成模块（HL7/FHIR、API网关）

### 5.2 AI开发建议
- 使用AI进行代码生成
- AI辅助文档撰写
- 自动化测试用例生成
- CI/CD流水线自动构建部署
- AI驱动的性能优化建议

### 5.3 技术参考资料
- CDISC SDTM Implementation Guide v3.
- CDASH Item Library v5.
- 21 CFR Part 11 - Electronic Records; Electronic Signatures
- GDPR - General Data Protection Regulation
- HIPAA - Health Insurance Portability and Accountability Act

---
**文档生成时间：2026年5月29日**