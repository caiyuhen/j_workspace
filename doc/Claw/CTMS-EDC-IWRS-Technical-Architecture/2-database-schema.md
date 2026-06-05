# CTMS+EDC+IWRS 平台 - 数据库 Schema 设计

**文档版本**: 1.0  
**创建日期**: 2026-05-27  
**作者**: 架构团队  
**状态**: 草案

---

## 1. 设计原则

### 1.1 命名规范

- **表名**: 小写字母 + 下划线（如：`edc_templates`）
- **字段名**: 小写字母 + 下划线（如：`created_at`）
- **主键**: `id` (UUID 类型)
- **外键**: `表名_singular_id`（如：`study_id`）
- **索引**: `idx_表名_字段名`
- **时间字段**: `created_at`, `updated_at`, `deleted_at`

### 1.2 多租户隔离

所有业务表必须包含 `tenant_id` 字段，并启用 **Row-Level Security (RLS)**。

### 1.3 CDISC 标准

- EDC 数据表遵循 CDASH 命名规范
- SDTM 导出表遵循 SDTM 标准结构
- 使用域标识符（Domain Identifier）区分数据类型

---

## 2. 核心实体关系图 (ER 图)

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    tenants      │         │     users       │         │    roles        │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │───────⟨ │ id (PK)         │         │ id (PK)         │
│ name            │   多    │ tenant_id (FK)  │         │ tenant_id (FK)  │
│ status          │         │ email           │         │ name            │
│ created_at      │         │ password_hash   │         │ permissions     │
└─────────────────┘         │ role_id (FK)    │         │ created_at      │
                            │ created_at      │         └─────────────────┘
                            └────────┬────────┘                  ▲
                                     │                           │
                                     ▼                           │
                            ┌─────────────────┐                  │
                            │   user_roles    │──────────────────┘
                            ├─────────────────┤
                            │ user_id (FK)    │
                            │ role_id (FK)    │
                            └─────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     studies     │         │     sites       │         │   protocols     │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │───────⟨ │ id (PK)         │         │ id (PK)         │
│ tenant_id (FK)  │   多    │ study_id (FK)   │         │ study_id (FK)   │
│ protocol_id     │         │ site_number     │         │ version         │
│ name            │         │ pi_name         │         │ text            │
│ status          │         │ status          │         │ effective_date  │
│ started_at      │         │ created_at      │         └─────────────────┘
│ created_at      │         └─────────────────┘
└────────┬────────┘
         │
         ├───⟨ ┌─────────────────┐
         │     │  edc_templates  │
         │     ├─────────────────┤
         │     │ id (PK)         │
         │     │ study_id (FK)   │
         │     │ name            │
         │     │ structure       │
         │     │ cdash_compliant │
         │     └─────────────────┘
         │
         ├───⟨ ┌─────────────────┐
         │     │   iwrs_config   │
         │     ├─────────────────┤
         │     │ id (PK)         │
         │     │ study_id (FK)   │
         │     │ algorithm       │
         │     │ treatment_arms  │
         │     └─────────────────┘
         │
         └───⟨ ┌─────────────────┐
               │   timesheets    │
               ├─────────────────┤
               │ id (PK)         │
               │ study_id (FK)   │
               │ user_id (FK)    │
               │ hours           │
               │ date            │
               └─────────────────┘
```

---

## 3. 认证服务数据库 (auth-service)

### 3.1 tenants 表（租户）

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    subscription_plan VARCHAR(50),
    max_users INT DEFAULT 100,
    max_studies INT DEFAULT 10,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenants_code ON tenants(code);
```

### 3.2 users 表（用户）

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(100),
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);

-- 启用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

### 3.3 roles 表（角色）

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_roles_tenant_code ON roles(tenant_id, code);
```

### 3.4 user_roles 表（用户 - 角色关联）

```sql
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);
```

### 3.5 sessions 表（会话）

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(token);
```

---

## 4. CTMS 服务数据库 (ctms-service)

### 4.1 studies 表（试验项目）

```sql
CREATE TABLE studies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    protocol_id UUID REFERENCES protocols(id),
    study_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    study_type VARCHAR(50),  -- 'interventional', 'observational'
    design VARCHAR(50),       -- 'RCT', 'single_arm', 'crossover'
    sponsor VARCHAR(255),
    principal_investigator VARCHAR(100),
    irb_name VARCHAR(255),
    status VARCHAR(20) DEFAULT 'planning',
    target_enrollment INT,
    actual_enrollment INT DEFAULT 0,
    start_date DATE,
    end_date DATE,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_studies_tenant ON studies(tenant_id);
CREATE INDEX idx_studies_status ON studies(status);
CREATE INDEX idx_studies_number ON studies(study_number);

ALTER TABLE studies ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON studies
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

### 4.2 protocols 表（方案）

```sql
CREATE TABLE protocols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    text TEXT,  -- 方案全文
    file_url VARCHAR(500),
    effective_date DATE,
    status VARCHAR(20) DEFAULT 'draft',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_protocols_tenant ON protocols(tenant_id);
```

### 4.3 sites 表（研究中心）

```sql
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    site_number VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    pi_name VARCHAR(100),
    pi_email VARCHAR(255),
    pi_phone VARCHAR(20),
    sub_investigators JSONB,  -- 子研究者列表
    target_enrollment INT,
    actual_enrollment INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'signed',
    activation_date DATE,
    close_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sites_study ON sites(study_id);
CREATE INDEX idx_sites_number ON sites(site_number);
```

### 4.4 timesheets 表（工时记录）

```sql
CREATE TABLE timesheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID REFERENCES studies(id) ON DELETE SET NULL,
    site_id UUID REFERENCES sites(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    hours DECIMAL(4, 2) NOT NULL,
    task_type VARCHAR(50),  -- 'data_entry', 'query_response', 'monitoring'
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    approval_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timesheets_study ON timesheets(study_id);
CREATE INDEX idx_timesheets_user ON timesheets(user_id);
CREATE INDEX idx_timesheets_date ON timesheets(date);
CREATE INDEX idx_timesheets_status ON timesheets(status);
```

### 4.5 budgets 表（收支管理）

```sql
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    site_id UUID REFERENCES sites(id) ON DELETE SET NULL,
    category VARCHAR(50),  -- 'payment', 'expense', 'milestone'
    type VARCHAR(50),      -- 'income', 'outcome'
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    description TEXT,
    due_date DATE,
    paid_date DATE,
    status VARCHAR(20) DEFAULT 'planned',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_budgets_study ON budgets(study_id);
CREATE INDEX idx_budgets_status ON budgets(status);
```

### 4.6 approvals 表（审批流程）

```sql
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,  -- 'timesheet', 'budget', 'deviation'
    entity_id UUID NOT NULL,
    workflow_name VARCHAR(100),
    current_step INT DEFAULT 1,
    total_steps INT,
    status VARCHAR(20) DEFAULT 'pending',
    approvers JSONB,  -- 审批链
    current_approver UUID REFERENCES users(id),
    submitted_by UUID NOT NULL REFERENCES users(id),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_approvals_entity ON approvals(entity_type, entity_id);
CREATE INDEX idx_approvals_status ON approvals(status);
```

---

## 5. EDC 服务数据库 (edc-service)

### 5.1 edc_templates 表（eCRF 模板）

```sql
CREATE TABLE edc_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(100),
    description TEXT,
    structure JSONB NOT NULL,  -- 表单结构定义
    cdash_compliant BOOLEAN DEFAULT TRUE,
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'draft',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_edc_templates_study ON edc_templates(study_id);
CREATE INDEX idx_edc_templates_status ON edc_templates(status);

ALTER TABLE edc_templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON edc_templates
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

### 5.2 crf_forms 表（CRF 表单实例）

```sql
CREATE TABLE crf_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES edc_templates(id) ON DELETE RESTRICT,
    subject_id VARCHAR(100) NOT NULL,  -- 受试者编号
    visit_name VARCHAR(100),
    form_data JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'draft',
    completed_at TIMESTAMP,
    completed_by UUID REFERENCES users(id),
    locked_at TIMESTAMP,
    locked_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_crf_forms_unique ON crf_forms(study_id, site_id, subject_id, template_id, visit_name);
CREATE INDEX idx_crf_forms_status ON crf_forms(status);

ALTER TABLE crf_forms ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON crf_forms
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

### 5.3 crf_fields 表（字段定义）

```sql
CREATE TABLE crf_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES edc_templates(id) ON DELETE CASCADE,
    field_key VARCHAR(100) NOT NULL,
    field_label VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL,  -- 'text', 'number', 'date', 'select', 'checkbox'
    cdash_variable VARCHAR(100),      -- CDASH 变量名
    required BOOLEAN DEFAULT FALSE,
    options JSONB,                    -- 下拉选项
    validation_rules JSONB,           -- 验证规则
    order_index INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crf_fields_template ON crf_fields(template_id);
```

### 5.4 edit_checks 表（核查规则）

```sql
CREATE TABLE edit_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    template_id UUID REFERENCES edc_templates(id),
    check_code VARCHAR(100) NOT NULL,
    check_name VARCHAR(255) NOT NULL,
    check_type VARCHAR(50),  -- 'hard', 'soft', 'warning'
    condition JSONB NOT NULL,  -- 条件表达式
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_edit_checks_study ON edit_checks(study_id);
CREATE INDEX idx_edit_checks_template ON edit_checks(template_id);
```

### 5.5 queries 表（质疑）

```sql
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    form_id UUID NOT NULL REFERENCES crf_forms(id) ON DELETE CASCADE,
    field_key VARCHAR(100),
    query_type VARCHAR(50),  -- 'edit_check', 'manual', 'resolving'
    question TEXT NOT NULL,
    answer TEXT,
    status VARCHAR(20) DEFAULT 'open',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP
);

CREATE INDEX idx_queries_form ON queries(form_id);
CREATE INDEX idx_queries_status ON queries(status);
CREATE INDEX idx_queries_study ON queries(study_id);
```

### 5.6 ae_events 表（不良事件）

```sql
CREATE TABLE ae_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    subject_id VARCHAR(100) NOT NULL,
    ae_term VARCHAR(255) NOT NULL,      -- 不良事件名称
    ae_start_date DATE NOT NULL,         -- 开始日期
    ae_end_date DATE,                    -- 结束日期
    ae_severity VARCHAR(50),             -- 严重程度
    ae_outcome VARCHAR(50),              -- 转归
    ae_action_taken TEXT,                -- 采取的措施
    ae_causality VARCHAR(50),            -- 因果关系
    ae_serious BOOLEAN DEFAULT FALSE,    -- 是否 SAE
    ae_hospitalization BOOLEAN DEFAULT FALSE,
    ae_disability BOOLEAN DEFAULT FALSE,
    ae_life_threatening BOOLEAN DEFAULT FALSE,
    ae_death BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ae_events_study ON ae_events(study_id);
CREATE INDEX idx_ae_events_subject ON ae_events(subject_id);
CREATE INDEX idx_ae_events_serious ON ae_events(ae_serious);
```

---

## 6. IWRS 服务数据库 (iwrs-service)

### 6.1 iwrs_config 表（随机化配置）

```sql
CREATE TABLE iwrs_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID UNIQUE NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    algorithm VARCHAR(50) NOT NULL,  -- 'simple', 'block', 'stratified', 'dynamic'
    treatment_arms JSONB NOT NULL,  -- 治疗臂配置
    block_sizes INT[],               -- 区组大小
    stratification_factors JSONB,   -- 分层因素
    allocation_ratio INT[],          -- 分配比例
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_iwrs_config_study ON iwrs_config(study_id);
```

### 6.2 randomizations 表（随机化记录）

```sql
CREATE TABLE randomizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    subject_id VARCHAR(100) NOT NULL,
    randomization_id VARCHAR(100) UNIQUE NOT NULL,  -- 随机化编号
    treatment_arm VARCHAR(100) NOT NULL,
    stratification_values JSONB,
    is_blinded BOOLEAN DEFAULT TRUE,
    randomized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    randomized_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_randomizations_subject ON randomizations(study_id, site_id, subject_id);
CREATE INDEX idx_randomizations_id ON randomizations(randomization_id);

-- 随机化编号索引（快速查询）
CREATE INDEX idx_randomizations_lookup ON randomizations(randomization_id);
```

### 6.3 unblinding 表（破盲记录）

```sql
CREATE TABLE unblinding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    randomization_id UUID NOT NULL REFERENCES randomizations(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    requested_by UUID NOT NULL REFERENCES users(id),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE INDEX idx_unblinding_randomization ON unblinding(randomization_id);
```

### 6.4 drug_inventory 表（药物库存）

```sql
CREATE TABLE drug_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
    site_id UUID REFERENCES sites(id),
    drug_name VARCHAR(255) NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    specification VARCHAR(100),
    quantity INT NOT NULL,
    unit VARCHAR(50),
    expiration_date DATE,
    storage_condition VARCHAR(100),
    status VARCHAR(20) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_drug_inventory_study ON drug_inventory(study_id);
CREATE INDEX idx_drug_inventory_site ON drug_inventory(site_id);
CREATE INDEX idx_drug_inventory_expiration ON drug_inventory(expiration_date);
```

### 6.5 drug_distribution 表（药物分发）

```sql
CREATE TABLE drug_distribution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID NOT NULL REFERENCES drug_inventory(id) ON DELETE RESTRICT,
    subject_id VARCHAR(100) NOT NULL,
    visit_name VARCHAR(100),
    quantity INT NOT NULL,
    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    distributed_by UUID NOT NULL REFERENCES users(id),
    return_quantity INT DEFAULT 0,
    return_date DATE,
    reason_for_return TEXT
);

CREATE INDEX idx_drug_distribution_subject ON drug_distribution(subject_id);
```

---

## 7. 安全服务数据库 (security-service)

### 7.1 audit_logs 表（审计追踪）

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,  -- 实体类型
    entity_id UUID NOT NULL,            -- 实体 ID
    action VARCHAR(50) NOT NULL,        -- CREATE, UPDATE, DELETE, LOGIN, EXPORT
    old_value JSONB,                    -- 旧值
    new_value JSONB,                    -- 新值
    user_id UUID REFERENCES users(id),  -- 操作人
    user_name VARCHAR(100),             -- 操作人姓名（冗余，防删除）
    ip_address INET,                    -- IP 地址
    user_agent TEXT,                    -- User-Agent
    reason TEXT,                        -- 操作原因
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 按实体类型和时间索引
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);

-- 审计日志不可删除（符合 21 CFR Part 11）
-- 不创建删除触发器，只允许 INSERT

-- 分区（按月份）
CREATE TABLE audit_logs_2026_05 (
    CHECK (timestamp >= '2026-05-01' AND timestamp < '2026-06-01')
) INHERITS (audit_logs);
```

### 7.2 electronic_signatures 表（电子签名）

```sql
CREATE TABLE electronic_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    signed_entity_type VARCHAR(100),
    signed_entity_id UUID,
    signature_type VARCHAR(50),  -- 'simple', 'advanced', 'qualified'
    signature_value TEXT NOT NULL,
    reason_for_signature TEXT,
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    certificate_url VARCHAR(500)
);

CREATE INDEX idx_electronic_signatures_user ON electronic_signatures(user_id);
CREATE INDEX idx_electronic_signatures_entity ON electronic_signatures(signed_entity_type, signed_entity_id);
```

---

## 8. 数据字典与枚举

### 8.1 试验状态枚举

```sql
CREATE TYPE study_status AS ENUM (
    'planning',    -- 方案中
    'approved',    -- 已批准
    'recruiting',  -- 入组中
    'active',      -- 进行中
    'completed',   -- 已完成
    'terminated'   -- 已终止
);
```

### 8.2 表单状态枚举

```sql
CREATE TYPE form_status AS ENUM (
    'draft',       -- 草稿
    'completed',   -- 已完成
    'reviewed',    -- 已审核
    'locked'       -- 已锁定
);
```

### 8.3 质疑状态枚举

```sql
CREATE TYPE query_status AS ENUM (
    'open',        -- 未解决
    'answered',    -- 已回复
    'resolving',   -- 解决中
    'resolved'     -- 已解决
);
```

---

## 9. 索引优化策略

### 9.1 复合索引

```sql
-- 租户 + 状态（最常见查询模式）
CREATE INDEX idx_studies_tenant_status ON studies(tenant_id, status);
CREATE INDEX idx_users_tenant_status ON users(tenant_id, status);

-- 试验 + 中心 + 受试者（EDC 查询）
CREATE INDEX idx_crf_forms_hierarchy ON crf_forms(study_id, site_id, subject_id);

-- 时间范围查询
CREATE INDEX idx_timesheets_date_range ON timesheets(date DESC);
CREATE INDEX idx_audit_logs_time_range ON audit_logs(timestamp DESC);
```

### 9.2 部分索引

```sql
-- 仅索引未解决的质疑
CREATE INDEX idx_queries_open ON queries(study_id) WHERE status = 'open';

-- 仅索引进行中的试验
CREATE INDEX idx_studies_active ON studies(tenant_id) WHERE status IN ('recruiting', 'active');
```

---

## 10. 数据归档策略

### 10.1 审计日志归档

```sql
-- 每月分区表
CREATE TABLE audit_logs_2026_06 (
    CHECK (timestamp >= '2026-06-01' AND timestamp < '2026-07-01')
) INHERITS (audit_logs);

-- 归档旧数据（3 年前的日志移到冷存储）
CREATE OR REPLACE FUNCTION archive_audit_logs()
RETURNS void AS $$
BEGIN
    INSERT INTO audit_logs_archive
    SELECT * FROM audit_logs
    WHERE timestamp < CURRENT_DATE - INTERVAL '3 years';
    
    -- 注意：不删除主表数据，符合合规要求
END;
$$ LANGUAGE plpgsql;
```

---

## 11. 迁移脚本示例

### 11.1 初始化租户

```sql
-- 创建默认租户
INSERT INTO tenants (id, name, code, status)
VALUES (
    gen_random_uuid(),
    '示例租户',
    'demo',
    'active'
) ON CONFLICT (code) DO NOTHING;
```

### 11.2 创建管理员用户

```sql
INSERT INTO users (id, tenant_id, email, password_hash, name, role_id)
SELECT
    gen_random_uuid(),
    t.id,
    'admin@example.com',
    '$2b$12$...',  -- bcrypt 加密的密码
    '系统管理员',
    r.id
FROM tenants t
JOIN roles r ON r.tenant_id = t.id AND r.code = 'admin'
WHERE t.code = 'demo'
LIMIT 1;
```

---

**文档结束**

**下一步**: 
- 生成 Prisma Schema 文件
- 创建数据库迁移脚本
- 编写种子数据（Seed Data）
