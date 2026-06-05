# 医疗临床试验平台 - 详细技术设计文档

## 一、总体架构设计

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        API 网关层                                │
│  (Kong/Nginx + JWT 认证 + 限流 + 日志)                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                      服务注册中心                              │
│                   (Consul/Eureka)                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                      微服务层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ CTMS 服务 │  │ EDC 服务  │  │ IWRS 服务 │  │ 病历夹服务 │       │
│  │          │  │          │  │          │  │          │       │
│  │ 试验管理  │  │ 表单设计  │  │ 随机化   │  │ 患者管理  │       │
│  │ 中心管理  │  │ 数据录入  │  │ 药物管理  │  │ 诊疗记录  │       │
│  │ eTMF     │  │ 数据验证  │  │ 入组流程  │  │ 自定义表单│       │
│  │ 工时管理  │  │ 审计追踪  │  │          │  │          │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│         │            │            │            │                │
│         └────────────┴────────────┴────────────┘                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                    数据访问层                                    │
│         (MyBatis-Plus + 多租户隔离 + 连接池)                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                   PostgreSQL 数据库                              │
│  (多租户 Schema + 行级安全 + 读写分离)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈选型

#### 后端技术栈
- **开发语言**: Java 17 / Spring Boot 3.x
- **微服务框架**: Spring Cloud Alibaba
- **服务注册/配置**: Nacos
- **API 网关**: Spring Cloud Gateway
- **服务调用**: OpenFeign
- **熔断降级**: Sentinel
- **日志追踪**: SkyWalking
- **ORM 框架**: MyBatis-Plus
- **数据库**: PostgreSQL 15+
- **缓存**: Redis 7.x
- **消息队列**: RabbitMQ / Kafka

#### 前端技术栈
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design 5
- **状态管理**: Zustand
- **HTTP 客户端**: Axios
- **表单库**: React Hook Form
- **数据可视化**: ECharts
- **拖拽库**: React DnD

#### DevOps 工具
- **容器化**: Docker + Kubernetes
- **CI/CD**: Jenkins / GitLab CI
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack (Elasticsearch + Logstash + Kibana)
- **代码质量**: SonarQube

---

## 二、数据库设计

### 2.1 多租户架构设计

#### 租户隔离策略
```sql
-- 方案 1: Schema 隔离（推荐）
CREATE SCHEMA tenant_001;
CREATE SCHEMA tenant_002;
-- 每个租户独立 Schema，数据完全隔离

-- 方案 2: 行级隔离
-- 所有租户数据在同一表，通过 tenant_id 字段隔离
CREATE TABLE patients (
    tenant_id UUID NOT NULL,
    patient_id BIGSERIAL,
    -- ... 其他字段
    PRIMARY KEY (tenant_id, patient_id)
);
```

#### 推荐的 PostgreSQL 多租户实现
```sql
-- 启用行级安全 (RLS)
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- 创建 RLS 策略
CREATE POLICY tenant_isolation ON patients
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- 设置租户上下文
SET app.current_tenant = 'uuid-here';
```

### 2.2 核心表结构设计

#### 2.2.1 租户与用户表
```sql
-- 租户表
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code VARCHAR(50) UNIQUE NOT NULL,  -- 租户编码
    tenant_name VARCHAR(100) NOT NULL,        -- 租户名称
    subscription_tier VARCHAR(50),            -- 订阅级别
    max_users INTEGER DEFAULT 10,             -- 最大用户数
    max_trials INTEGER DEFAULT 5,             -- 最大试验数
    status VARCHAR(20) DEFAULT 'active',      -- 状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expired_at TIMESTAMP,                     -- 到期时间
    config JSONB DEFAULT '{}'                 -- 租户配置
);

-- 用户表
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    real_name VARCHAR(50),
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',      -- active, inactive, locked
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    CONSTRAINT fk_user_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- 角色表
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    role_code VARCHAR(50) UNIQUE NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',           -- 权限列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

-- 用户角色关联表
CREATE TABLE user_roles (
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
);
```

#### 2.2.2 CTMS 核心表
```sql
-- 试验项目表
CREATE TABLE trials (
    trial_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_code VARCHAR(50) UNIQUE NOT NULL,   -- 试验编号
    trial_name VARCHAR(200) NOT NULL,         -- 试验名称
    protocol_number VARCHAR(100),             -- 方案编号
    sponsor_name VARCHAR(200),                -- 申办方
    phase VARCHAR(20),                        -- I, II, III, IV期
    therapeutic_area VARCHAR(100),            -- 治疗领域
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'planning',    -- planning, active, completed, paused
    budget DECIMAL(15, 2),
    manager_id UUID,
    config JSONB DEFAULT '{}',                -- 试验配置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES users(user_id)
);

-- 研究中心表
CREATE TABLE study_sites (
    site_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    site_code VARCHAR(50) NOT NULL,           -- 中心编号
    site_name VARCHAR(200) NOT NULL,          -- 中心名称
    hospital_name VARCHAR(200),               -- 医院名称
    address TEXT,                             -- 详细地址
    city VARCHAR(50),
    province VARCHAR(50),
    country VARCHAR(50) DEFAULT 'China',
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    gcp_certificate VARCHAR(100),             -- GCP 证书编号
    gcp_expiry DATE,                          -- GCP 证书到期
    principal_investigator_id UUID,           -- 主要研究者
    status VARCHAR(20) DEFAULT 'pending',     -- pending, approved, inactive
    enrollment_target INTEGER,                -- 计划入组数
    enrolled_count INTEGER DEFAULT 0,         -- 已入组数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (principal_investigator_id) REFERENCES users(user_id)
);

-- 研究者表
CREATE TABLE investigators (
    investigator_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    site_id UUID NOT NULL,
    user_id UUID,
    name VARCHAR(50) NOT NULL,
    title VARCHAR(100),                       -- 职称
    specialty VARCHAR(100),                   -- 专业
    qualification VARCHAR(100),               -- 资质
    gcp_certificate_date DATE,                -- GCP 培训日期
    signature_image VARCHAR(500),             -- 签名图片
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES study_sites(site_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- eTMF 文档表
CREATE TABLE etmf_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    document_code VARCHAR(50),
    document_name VARCHAR(200) NOT NULL,
    document_type VARCHAR(50),                -- 文档类型 (ISTAF 分类)
    category VARCHAR(50),                     -- 分类
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'draft',       -- draft, submitted, approved, archived
    file_path VARCHAR(500),
    file_size BIGINT,
    file_type VARCHAR(50),
    uploader_id UUID,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by UUID,
    approved_at TIMESTAMP,
    approval_notes TEXT,
    parent_document_id UUID,                  -- 父文档 ID
    version_notes TEXT,
    metadata JSONB DEFAULT '{}',
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (uploader_id) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id),
    FOREIGN KEY (parent_document_id) REFERENCES etmf_documents(document_id)
);

-- 工时表
CREATE TABLE work_hours (
    work_hour_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    trial_id UUID,
    project_task VARCHAR(100),                -- 任务描述
    work_date DATE NOT NULL,
    hours DECIMAL(4, 2) NOT NULL,             -- 工时
    work_type VARCHAR(50),                    -- 工作类型
    notes TEXT,
    status VARCHAR(20) DEFAULT 'pending',     -- pending, approved, rejected
    manager_id UUID,
    approved_at TIMESTAMP,
    approval_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES users(user_id)
);
```

#### 2.2.3 EDC 核心表
```sql
-- 表单设计主表
CREATE TABLE crf_forms (
    form_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    form_code VARCHAR(50) NOT NULL,
    form_name VARCHAR(100) NOT NULL,
    form_version VARCHAR(20) DEFAULT '1.0',
    form_type VARCHAR(50),                    -- questionnaire, casebook
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    layout_config JSONB DEFAULT '{}',         -- 布局配置
    validation_rules JSONB DEFAULT '[]',      -- 验证规则
    cdash_mapping JSONB DEFAULT '{}',         -- CDASH 映射
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE
);

-- 表单字段定义表
CREATE TABLE crf_fields (
    field_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL,
    field_code VARCHAR(100) NOT NULL,         -- 字段编码 (CDASH 标准)
    field_name VARCHAR(100) NOT NULL,         -- 字段中文名
    field_type VARCHAR(50) NOT NULL,          -- text, number, date, select, radio, checkbox
    required BOOLEAN DEFAULT FALSE,
    readonly BOOLEAN DEFAULT FALSE,
    max_length INTEGER,
    min_value NUMERIC,
    max_value NUMERIC,
    default_value TEXT,
    options JSONB DEFAULT '[]',               -- 选项列表 (select/radio/checkbox)
    validation_pattern VARCHAR(200),          -- 正则验证
    validation_message TEXT,
    display_condition TEXT,                   -- 显示条件
    cdash_domain VARCHAR(50),                 -- CDASH 域
    sdtm_variable VARCHAR(100),               -- SDTM 变量名
    help_text TEXT,                           -- 帮助文本
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (form_id) REFERENCES crf_forms(form_id) ON DELETE CASCADE
);

-- 访视表
CREATE TABLE visits (
    visit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    visit_code VARCHAR(50) NOT NULL,          -- 访视编码 (SCREENING, BASELINE, V1, V2...)
    visit_name VARCHAR(100) NOT NULL,         -- 访视名称
    visit_day_min INTEGER,                    -- 最小天数
    visit_day_max INTEGER,                    -- 最大天数
    visit_duration_min INTEGER,               -- 最小持续天数
    visit_duration_max INTEGER,               -- 最大持续天数
    is_mandatory BOOLEAN DEFAULT TRUE,        -- 是否必填
    display_order INTEGER DEFAULT 0,
    form_ids UUID[],                          -- 关联表单 ID 数组
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE
);

-- 受试者表
CREATE TABLE subjects (
    subject_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    site_id UUID NOT NULL,
    subject_code VARCHAR(50) NOT NULL,        -- 受试者编号
    screen_fail_reason VARCHAR(200),          -- 筛选失败原因
    screen_date DATE,                         -- 筛选日期
    randomization_date DATE,                  -- 随机化日期
    randomization_num VARCHAR(50),            -- 随机号
    treatment_arm VARCHAR(50),                -- 治疗组
    enrollment_status VARCHAR(50),            -- enrolled, screened, withdrawn, completed
    withdrawal_date DATE,
    withdrawal_reason TEXT,
    date_of_birth DATE,
    gender VARCHAR(10),                       -- M, F, U
    ethnicity VARCHAR(50),
    height DECIMAL(5, 2),                     -- 身高 cm
    weight DECIMAL(5, 2),                     -- 体重 kg
    bmi DECIMAL(4, 2),
    status VARCHAR(20) DEFAULT 'screening',   -- screening, enrolled, active, completed, withdrawn
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES study_sites(site_id) ON DELETE CASCADE
);

-- 访视记录表
CREATE TABLE subject_visits (
    visit_record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    visit_id UUID NOT NULL,
    visit_date DATE,
    actual_day INTEGER,                       -- 实际第几天
    status VARCHAR(20) DEFAULT 'pending',     -- pending, completed, missed, skipped
    notes TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(visit_id) ON DELETE CASCADE
);

-- 表单数据表
CREATE TABLE form_data (
    data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    visit_record_id UUID NOT NULL,
    form_id UUID NOT NULL,
    form_version VARCHAR(20) NOT NULL,
    data_json JSONB NOT NULL,                 -- 表单数据 (JSON 格式)
    submitter_id UUID,
    submitted_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'draft',       -- draft, submitted, locked
    reviewer_id UUID,
    reviewed_at TIMESTAMP,
    review_status VARCHAR(20),                -- pending, approved, rejected
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (visit_record_id) REFERENCES subject_visits(visit_record_id) ON DELETE CASCADE,
    FOREIGN KEY (form_id) REFERENCES crf_forms(form_id) ON DELETE CASCADE,
    FOREIGN KEY (submitter_id) REFERENCES users(user_id),
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id)
);

-- 审计追踪表
CREATE TABLE audit_trail (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,         -- subjects, form_data, users 等
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,              -- CREATE, UPDATE, DELETE, VIEW
    field_name VARCHAR(100),
    old_value JSONB,
    new_value JSONB,
    user_id UUID NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 疑问 (Query) 表
CREATE TABLE queries (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    visit_record_id UUID,
    form_id UUID,
    field_code VARCHAR(100),
    query_title VARCHAR(200) NOT NULL,
    query_description TEXT NOT NULL,
    query_status VARCHAR(20) DEFAULT 'open',  -- open, resolved, closed
    priority VARCHAR(20) DEFAULT 'medium',    -- low, medium, high, urgent
    assigned_to UUID,                         -- 分配给谁
    creator_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by UUID,
    resolution_notes TEXT,
    response_notes TEXT,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (visit_record_id) REFERENCES subject_visits(visit_record_id) ON DELETE SET NULL,
    FOREIGN KEY (form_id) REFERENCES crf_forms(form_id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_to) REFERENCES users(user_id),
    FOREIGN KEY (creator_id) REFERENCES users(user_id),
    FOREIGN KEY (resolved_by) REFERENCES users(user_id)
);
```

#### 2.2.4 SDTM 数据模型表
```sql
-- SDTM: 受试者特征 (Domain: DM)
CREATE TABLE sdtm_dm (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    -- 标准变量
    STUDYID VARCHAR(200),
    USUBJID VARCHAR(100),           -- 唯一受试者 ID
    SUBJID VARCHAR(50),             -- 受试者编号
    RMSTCD VARCHAR(10),             -- 随机化方法代码
    RMSTRTCD VARCHAR(10),           -- 随机化治疗代码
    ACTARMCD VARCHAR(10),           -- 实际治疗代码
    ACTARMLN VARCHAR(100),          -- 实际治疗描述
    COUNTRY VARCHAR(100),           -- 国家
    STATE VARCHAR(100),             -- 州/省
    SITEID VARCHAR(50),             -- 中心编号
    SITEONTR VARCHAR(100),          -- 中心名称
    SEXF VARCHAR(1),                -- 性别
    RACEF VARCHAR(100),             -- 种族
    ETHNIC VARCHAR(10),             -- 民族
    SPRTRTFL VARCHAR(1),            -- 入组标志
    SPRTRT VARCHAR(100),            -- 入组治疗
    DTHFL VARCHAR(1),               -- 死亡标志
    DTHDT DATE,                     -- 死亡日期
    -- 其他元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE
);

-- SDTM: 受试者筛选 (Domain: Screen)
CREATE TABLE sdtm_screen (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    -- 标准变量
    STUDYID VARCHAR(200),
    USUBJID VARCHAR(100),
    SCREENF VARCHAR(1),             -- 筛选标志
    SCREENDT DATE,                  -- 筛选日期
    SCREASFL VARCHAR(1),            -- 筛选结果
    SCRREASN TEXT,                  -- 筛选失败原因
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SDTM: 不良事件 (Domain: AE)
CREATE TABLE sdtm_ae (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    -- 标准变量
    STUDYID VARCHAR(200),
    USUBJID VARCHAR(100),
    AESEQR VARCHAR(10),             -- 序列号
    AETERM VARCHAR(200),            -- 不良事件术语
    AEDECOD VARCHAR(200),           -- 解码术语
    AEBODSYS VARCHAR(200),          -- 系统器官分类
    AESEV VARCHAR(20),              -- 严重程度 (Mild, Moderate, Severe)
    AEREL VARCHAR(20),              -- 相关性 (Not related, Related, Possible...)
    AESTDTC DATE,                   -- 开始日期
    AEENDTC DATE,                   -- 结束日期
    AEOUT VARCHAR(20),              -- 结果 (Recovered, Not recovered...)
    AESER VARCHAR(1),               -- 严重事件标志
    AECONTRT VARCHAR(1),            -- 与药物相关标志
    -- 其他字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SDTM: 实验室检查 (Domain: LB)
CREATE TABLE sdtm_lb (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    -- 标准变量
    STUDYID VARCHAR(200),
    USUBJID VARCHAR(100),
    LBOSEQ VARCHAR(10),             -- 序列号
    LBDOM VARCHAR(50),              -- 域
    LBCAT VARCHAR(100),             -- 分类
    LBTESTCD VARCHAR(100),          -- 测试代码
    LBTEST VARCHAR(200),            -- 测试名称
    LBORRES VARCHAR(100),           -- 原始结果
    LBORRESU VARCHAR(50),           -- 原始单位
    LBNRLCD VARCHAR(100),           -- 正常范围代码
    LBNRLO NUMERIC,                 -- 正常范围下限
    LBNRHI NUMERIC,                 -- 正常范围上限
    LBORNRFL VARCHAR(1),            -- 正常范围标志
    LBSTRESC VARCHAR(100),          -- 结果字符串
    LBSTRESN NUMERIC,               -- 结果数值
    LBSTRESU VARCHAR(50),           -- 结果单位
    LBSPCA VARCHAR(20),             -- 标本类型
    LBDT DATE,                      -- 检测日期
    -- 其他字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.2.5 IWRS 核心表
```sql
-- 随机化方案表
CREATE TABLE randomization_schemes (
    scheme_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    scheme_name VARCHAR(100) NOT NULL,
    scheme_type VARCHAR(50),        -- simple, block, stratified, minimization
    description TEXT,
    treatment_arms JSONB NOT NULL,  -- 治疗组配置
    block_sizes INTEGER[],          -- 区组大小
    stratification_factors JSONB,   -- 分层因素
    minimization_params JSONB,      -- 最小化参数
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE
);

-- 药物配置表
CREATE TABLE drug_configs (
    drug_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    drug_code VARCHAR(50) NOT NULL,
    drug_name VARCHAR(100) NOT NULL,
    drug_type VARCHAR(50),          -- drug, placebo
    packaging VARCHAR(50),          -- 包装规格
    storage_condition TEXT,         -- 储存条件
    expiry_days INTEGER,            -- 有效期天数
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE
);

-- 药物库存表
CREATE TABLE drug_inventory (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    drug_id UUID NOT NULL,
    site_id UUID NOT NULL,
    batch_number VARCHAR(100),      -- 批次号
    quantity INTEGER NOT NULL,      -- 库存数量
    expiry_date DATE,               -- 有效期
    status VARCHAR(20) DEFAULT 'available', -- available, reserved, used, expired
    location VARCHAR(100),          -- 存放位置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (drug_id) REFERENCES drug_configs(drug_id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES study_sites(site_id) ON DELETE CASCADE
);

-- 随机化请求记录表
CREATE TABLE randomization_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    site_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    scheme_id UUID NOT NULL,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    requested_by UUID NOT NULL,
    stratification_factors JSONB,   -- 分层因素值
    randomization_result JSONB,     -- 随机化结果
    treatment_arm VARCHAR(50),      -- 分配治疗组
    randomization_num VARCHAR(50),  -- 随机号
    drug_allocation JSONB,          -- 药物分配
    ip_address VARCHAR(50),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES study_sites(site_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (scheme_id) REFERENCES randomization_schemes(scheme_id) ON DELETE CASCADE,
    FOREIGN KEY (requested_by) REFERENCES users(user_id)
);

-- 药物分配记录表
CREATE TABLE drug_allocations (
    allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    site_id UUID NOT NULL,
    randomization_request_id UUID NOT NULL,
    drug_id UUID NOT NULL,
    drug_code VARCHAR(50) NOT NULL,
    batch_number VARCHAR(100),
    quantity INTEGER NOT NULL,
    allocated_date DATE NOT NULL,
    allocated_by UUID NOT NULL,
    delivery_status VARCHAR(20) DEFAULT 'pending', -- pending, shipped, received, used
    delivery_date DATE,
    returned_quantity INTEGER DEFAULT 0,
    destroyed_quantity INTEGER DEFAULT 0,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES study_sites(site_id) ON DELETE CASCADE,
    FOREIGN KEY (randomization_request_id) REFERENCES randomization_requests(request_id) ON DELETE CASCADE,
    FOREIGN KEY (drug_id) REFERENCES drug_configs(drug_id) ON DELETE CASCADE,
    FOREIGN KEY (allocated_by) REFERENCES users(user_id)
);
```

#### 2.2.6 医生病历夹核心表
```sql
-- 患者病历夹主表
CREATE TABLE patient_clinical_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    doctor_id UUID NOT NULL,
    patient_external_id VARCHAR(100), -- 患者外部 ID
    patient_name VARCHAR(50),
    patient_id_card VARCHAR(50),
    gender VARCHAR(10),
    date_of_birth DATE,
    phone VARCHAR(20),
    address TEXT,
    medical_history TEXT,             -- 既往病史
    allergy_history TEXT,             -- 过敏史
    family_history TEXT,              -- 家族病史
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 自定义表单定义表
CREATE TABLE patient_forms (
    form_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    doctor_id UUID NOT NULL,
    form_name VARCHAR(100) NOT NULL,
    form_code VARCHAR(50) UNIQUE NOT NULL,
    source_crf_form_id UUID,          -- 来源 EDC 表单 ID
    is_active BOOLEAN DEFAULT TRUE,
    fields_config JSONB NOT NULL,     -- 表单字段配置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (source_crf_form_id) REFERENCES crf_forms(form_id) ON DELETE SET NULL
);

-- 患者表单数据表
CREATE TABLE patient_form_data (
    data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_record_id UUID NOT NULL,
    form_id UUID NOT NULL,
    form_version VARCHAR(20) DEFAULT '1.0',
    visit_date DATE,
    data_json JSONB NOT NULL,         -- 表单数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_record_id) REFERENCES patient_clinical_records(record_id) ON DELETE CASCADE,
    FOREIGN KEY (form_id) REFERENCES patient_forms(form_id) ON DELETE CASCADE
);

-- 检查结果表
CREATE TABLE lab_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_record_id UUID NOT NULL,
    result_date DATE NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    test_code VARCHAR(100),
    result_value VARCHAR(200),
    result_unit VARCHAR(50),
    result_numeric NUMERIC,
    normal_range VARCHAR(100),
    abnormal_flag VARCHAR(10),        -- H, L, N
    test_type VARCHAR(50),            -- blood, urine, imaging
    facility_name VARCHAR(200),       -- 检验机构
    document_path VARCHAR(500),       -- 检验报告文件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_record_id) REFERENCES patient_clinical_records(record_id) ON DELETE CASCADE
);

-- 影像检查表
CREATE TABLE imaging_results (
    imaging_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_record_id UUID NOT NULL,
    imaging_date DATE NOT NULL,
    imaging_type VARCHAR(50),         -- CT, MRI, X-ray, Ultrasound
    body_part VARCHAR(100),           -- 检查部位
    finding TEXT,                     -- 影像所见
    impression TEXT,                  -- 影像诊断
    report_document VARCHAR(500),     -- 报告文档
    image_urls JSONB DEFAULT '[]',    -- 影像图片 URL 数组
    facility_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_record_id) REFERENCES patient_clinical_records(record_id) ON DELETE CASCADE
);

-- 处方表
CREATE TABLE prescriptions (
    prescription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_record_id UUID NOT NULL,
    prescription_date DATE NOT NULL,
    doctor_id UUID NOT NULL,
    drug_name VARCHAR(200) NOT NULL,
    drug_code VARCHAR(100),
    dosage VARCHAR(100),              -- 剂量
    frequency VARCHAR(100),           -- 频率
    duration VARCHAR(100),            -- 疗程
    administration_route VARCHAR(100), -- 给药途径
    instructions TEXT,                -- 使用说明
    prescription_type VARCHAR(50),    -- 西药，中药，中成药
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_record_id) REFERENCES patient_clinical_records(record_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(user_id)
);
```

### 2.3 数据库索引优化
```sql
-- 租户隔离索引
CREATE INDEX idx_subjects_tenant ON subjects(tenant_id);
CREATE INDEX idx_forms_tenant ON crf_forms(tenant_id);
CREATE INDEX idx_trial_site_tenant ON study_sites(tenant_id, trial_id);

-- 查询性能索引
CREATE INDEX idx_subjects_trial ON subjects(trial_id);
CREATE INDEX idx_subjects_site ON subjects(site_id);
CREATE INDEX idx_subject_visits_subject ON subject_visits(subject_id);
CREATE INDEX idx_form_data_visit ON form_data(visit_record_id);
CREATE INDEX idx_audit_trail_entity ON audit_trail(entity_type, entity_id);

-- CDISC 标准索引
CREATE INDEX idx_sdtm_dm_trial ON sdtm_dm(trial_id, subject_id);
CREATE INDEX idx_sdtm_ae_trial ON sdtm_ae(trial_id, subject_id);
```

---

## 三、微服务架构设计

### 3.1 服务拆分

| 服务名称 | 端口 | 功能模块 | 技术栈 |
|---------|------|---------|--------|
| api-gateway | 8080 | API 网关 | Spring Cloud Gateway |
| auth-service | 8081 | 认证授权 | Spring Security + JWT |
| user-service | 8082 | 用户管理 | Spring Boot + MyBatis-Plus |
| ctms-service | 8083 | CTMS 核心 | Spring Boot + Quartz |
| edc-service | 8084 | EDC 核心 | Spring Boot + RuleEngine |
| iwrs-service | 8085 | IWRS 核心 | Spring Boot + RandomizationAlgo |
| patient-service | 8086 | 医生病历夹 | Spring Boot |
| file-service | 8087 | 文件服务 | MinIO + Spring Boot |
| report-service | 8088 | 报表服务 | JasperReports |
| notification-service | 8089 | 通知服务 | RabbitMQ + Email/SMS |

### 3.2 服务间通信

```yaml
# OpenFeign 配置示例
feign:
  client:
    config:
      default:
        connect-timeout: 5000
        read-timeout: 10000
        logger-level: FULL

# 服务调用示例
@FeignClient(name = "edc-service", fallback = EDCServiceFallback.class)
public interface EDCServiceClient {
    @GetMapping("/api/forms/{formId}")
    CrfForm getForm(@PathVariable("formId") String formId);
    
    @PostMapping("/api/forms/validate")
    ValidationResult validateData(@RequestBody ValidationRequest request);
}
```

### 3.3 消息队列设计

```yaml
# RabbitMQ 配置
spring:
  rabbitmq:
    host: rabbitmq
    port: 5672
    username: guest
    password: guest
    virtual-host: /
    
# 队列定义
queues:
  form-submission: 表单提交队列
  data-validation: 数据验证队列
  audit-logging: 审计日志队列
  notification: 通知队列
  report-generation: 报表生成队列
```

### 3.4 缓存策略

```java
// Redis 缓存配置
@Configuration
public class CacheConfig {
    
    @Bean
    public CacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofHours(1))  // 默认 1 小时过期
            .serializeKeysWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new GenericJackson2JsonRedisSerializer()));
        
        return RedisCacheManager.builder(factory)
            .cacheDefaults(config)
            .withCacheConfiguration("forms", 
                RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofHours(24)))
            .withCacheConfiguration("users",
                RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofHours(2)))
            .build();
    }
}
```

---

## 四、CDISC 标准实现

### 4.1 CDASH 字段映射

```sql
-- eCRF 字段 → CDASH 映射示例
INSERT INTO cdash_mapping (
    field_code,
    field_name,
    cdash_domain,
    cdash_variable,
    sdtm_variable,
    value_set
) VALUES
    ('SUBJID', '受试者编号', 'DM', 'SUBJID', 'SUBJID', NULL),
    ('RANDDATE', '随机化日期', 'DM', 'RANDDT', 'RANDDT', NULL),
    ('AGE', '年龄', 'DM', 'AGE', 'AGE', NULL),
    ('SEX', '性别', 'DM', 'SEX', 'SEX', 'M|F|U'),
    ('WEIGHT', '体重', 'EX', 'WT', 'WT', NULL),
    ('HEIGHT', '身高', 'EX', 'HT', 'HT', NULL),
    ('BMI', '体重指数', 'EX', 'BMI', 'BMI', NULL),
    ('LBTESTCD', '实验室检查代码', 'LB', 'LBTESTCD', 'LBTESTCD', NULL),
    ('LBORRES', '实验室原始结果', 'LB', 'LBORRES', 'LBORRES', NULL),
    ('AETERM', '不良事件术语', 'AE', 'AETERM', 'AETERM', NULL),
    ('AESEV', '不良事件严重程度', 'AE', 'AESEV', 'AESEV', 'Mild|Moderate|Severe');
```

### 4.2 SDTM 数据转换规则

```java
@Component
public class SDTMConverter {
    
    /**
     * 将 eCRF 数据转换为 SDTM 格式
     */
    public List<SdtmDm> convertToSDTM(List<FormEntry> formEntries, Trial trial) {
        return formEntries.stream()
            .map(entry -> {
                SdtmDm dm = new SdtmDm();
                dm.setSTUDYID(trial.getTrialCode());
                dm.setUSUBJID(entry.getSubjectCode());
                dm.setSUBJID(entry.getSubjectCode());
                dm.setRMSTRTCD(entry.getTreatmentArm());
                dm.setSEX(entry.getGender());
                dm.setRACEF(entry.getEthnicity());
                dm.setSPRTRTFL("Y");
                dm.setSPRTRT(entry.getTreatmentArm());
                return dm;
            })
            .collect(Collectors.toList());
    }
    
    /**
     * SDTM 验证
     */
    public ValidationResult validateSDTM(List<SdtmDm> dmList) {
        ValidationResult result = new ValidationResult();
        
        // 检查必填字段
        for (SdtmDm dm : dmList) {
            if (StringUtils.isEmpty(dm.getUSUBJID())) {
                result.addError("USUBJID is required");
            }
            if (StringUtils.isEmpty(dm.getRMSTRTCD())) {
                result.addError("RMSTRTCD is required");
            }
        }
        
        // 检查唯一性
        Set<String> uniqueIds = dmList.stream()
            .map(SdtmDm::getUSUBJID)
            .collect(Collectors.toSet());
        if (uniqueIds.size() != dmList.size()) {
            result.addError("Duplicate USUBJID found");
        }
        
        return result;
    }
}
```

---

## 五、安全性设计

### 5.1 JWT 认证

```java
@Component
public class JwtTokenProvider {
    
    private static final SecretKey SECRET_KEY = Keys.hmacShaKeyFor(
        "404e74476250655368566d597133743677397a2443262a484241644548234137".getBytes()
    );
    
    public String generateToken(UserDetails userDetails) {
        return Jwts.builder()
            .setSubject(userDetails.getUsername())
            .claim("userId", userDetails.getId())
            .claim("tenantId", userDetails.getTenantId())
            .claim("roles", userDetails.getAuthorities())
            .setIssuedAt(new Date(System.currentTimeMillis()))
            .setExpiration(new Date(System.currentTimeMillis() + 86400000)) // 24 小时
            .signWith(SECRET_KEY)
            .compact();
    }
    
    public String getTenantIdFromToken(String token) {
        Claims claims = Jwts.parser()
            .verifyWith(SECRET_KEY)
            .build()
            .parseSignedClaims(token)
            .getPayload();
        return claims.get("tenantId", String.class);
    }
}
```

### 5.2 数据加密

```java
@Component
public class DataEncryptionService {
    
    private static final String ALGORITHM = "AES";
    private static final String TRANSFORMATION = "AES/CBC/PKCS5Padding";
    private static final byte[] IV = "1234567890123456".getBytes(); // 16 字节
    
    @Value("${encryption.key}")
    private String encryptionKey;
    
    /**
     * 加密敏感数据
     */
    public String encrypt(String plainText) throws Exception {
        SecretKeySpec keySpec = new SecretKeySpec(encryptionKey.getBytes(), ALGORITHM);
        IvParameterSpec ivSpec = new IvParameterSpec(IV);
        
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(Cipher.ENCRYPT_MODE, keySpec, ivSpec);
        
        byte[] encrypted = cipher.doFinal(plainText.getBytes());
        return Base64.getEncoder().encodeToString(encrypted);
    }
    
    /**
     * 解密敏感数据
     */
    public String decrypt(String encryptedText) throws Exception {
        SecretKeySpec keySpec = new SecretKeySpec(encryptionKey.getBytes(), ALGORITHM);
        IvParameterSpec ivSpec = new IvParameterSpec(IV);
        
        Cipher cipher = Cipher.getInstance(TRANSFORMATION);
        cipher.init(Cipher.DECRYPT_MODE, keySpec, ivSpec);
        
        byte[] decoded = Base64.getDecoder().decode(encryptedText);
        byte[] decrypted = cipher.doFinal(decoded);
        return new String(decrypted);
    }
}
```

---

## 六、部署架构

### 6.1 Kubernetes 部署

```yaml
# deployment.yaml 示例
apiVersion: apps/v1
kind: Deployment
metadata:
  name: edc-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: edc-service
  template:
    metadata:
      labels:
        app: edc-service
    spec:
      containers:
      - name: edc-service
        image: registry.example.com/edc-service:latest
        ports:
        - containerPort: 8084
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "prod"
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: host
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8084
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8084
          initialDelaySeconds: 30
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: edc-service
spec:
  selector:
    app: edc-service
  ports:
  - port: 8084
    targetPort: 8084
  type: ClusterIP
```

---

## 七、监控与日志

### 7.1 Prometheus + Grafana

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'spring-boot-services'
    static_configs:
      - targets: ['edc-service:8084', 'ctms-service:8083', 'iwrs-service:8085']
    metrics_path: '/actuator/prometheus'
```

### 7.2 SkyWalking 链路追踪

```java
@Service
@Traced(value = "edc-service")
public class FormDataService {
    
    @Distributed(name = "validateFormData")
    public ValidationResult validateData(FormData data) {
        // 业务逻辑
    }
}
```

---

## 八、性能优化

### 8.1 数据库优化
- 读写分离
- 连接池优化 (HikariCP)
- 索引优化
- 查询缓存
- 批量操作

### 8.2 缓存优化
- Redis 集群
- 本地缓存 (Caffeine)
- 多级缓存策略

### 8.3 异步处理
- 异步数据验证
- 异步报表生成
- 异步消息通知

---

*文档版本：v1.0*
*创建日期：2026 年*
*维护人：蔡宇恒*
