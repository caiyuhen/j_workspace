# 医疗临床试验平台 - 数据库 ER 图设计

## 一、整体 ER 图架构

```mermaid
erDiagram
    TENANTS ||--o{ USERS : "1:N"
    TENANTS ||--o{ TRIALS : "1:N"
    USERS ||--o{ USER_ROLES : "1:N"
    USERS ||--o{ WORK_HOURS : "1:N"
    
    TRIALS ||--o{ STUDY_SITES : "1:N"
    TRIALS ||--o{ CRF_FORMS : "1:N"
    TRIALS ||--o{ VISITS : "1:N"
    TRIALS ||--o{ SUBJECTS : "1:N"
    TRIALS ||--o{ RANDOMIZATION_SCHEMES : "1:N"
    
    STUDY_SITES ||--o{ INVESTIGATORS : "1:N"
    STUDY_SITES ||--o{ SUBJECTS : "1:N"
    STUDY_SITES ||--o{ DRUG_INVENTORY : "1:N"
    STUDY_SITES ||--o{ RANDOMIZATION_REQUESTS : "1:N"
    
    CRF_FORMS ||--o{ CRF_FIELDS : "1:N"
    CRF_FORMS ||--o{ FORM_DATA : "1:N"
    
    VISITS ||--o{ SUBJECT_VISITS : "1:N"
    SUBJECT_VISITS ||--o{ FORM_DATA : "1:N"
    
    SUBJECTS ||--o{ SUBJECT_VISITS : "1:N"
    SUBJECTS ||--o{ RANDOMIZATION_REQUESTS : "1:N"
    SUBJECTS ||--o{ SDTM_DM : "1:N"
    SUBJECTS ||--o{ SDTM_AE : "1:N"
    SUBJECTS ||--o{ SDTM_LB : "1:N"
    SUBJECTS ||--o{ PATIENT_CLINICAL_RECORDS : "1:N"
    
    PATIENT_CLINICAL_RECORDS ||--o{ PATIENT_FORMS : "1:N"
    PATIENT_CLINICAL_RECORDS ||--o{ PATIENT_FORM_DATA : "1:N"
    PATIENT_CLINICAL_RECORDS ||--o{ LAB_RESULTS : "1:N"
    PATIENT_CLINICAL_RECORDS ||--o{ IMAGING_RESULTS : "1:N"
    PATIENT_CLINICAL_RECORDS ||--o{ PRESCRIPTIONS : "1:N"
    
    ETMF_DOCUMENTS ||--o{ ETMF_DOCUMENTS : "self-referencing"
    
    RANDOMIZATION_SCHEMES ||--o{ RANDOMIZATION_REQUESTS : "1:N"
    RANDOMIZATION_REQUESTS ||--o{ DRUG_ALLOCATIONS : "1:N"
    DRUG_CONFIGS ||--o{ DRUG_INVENTORY : "1:N"
    DRUG_CONFIGS ||--o{ DRUG_ALLOCATIONS : "1:N"
    
    ROLES ||--o{ USER_ROLES : "1:N"
```

---

## 二、租户与用户管理 ER 图

```mermaid
erDiagram
    TENANTS {
        UUID tenant_id PK
        VARCHAR tenant_code UK
        VARCHAR tenant_name
        VARCHAR subscription_tier
        INTEGER max_users
        INTEGER max_trials
        VARCHAR status
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP expired_at
        JSONB config
    }
    
    USERS {
        UUID user_id PK
        UUID tenant_id FK
        VARCHAR username UK
        VARCHAR email UK
        VARCHAR phone
        VARCHAR real_name
        VARCHAR password_hash
        VARCHAR avatar_url
        VARCHAR status
        TIMESTAMP last_login_at
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    ROLES {
        UUID role_id PK
        UUID tenant_id FK
        VARCHAR role_code UK
        VARCHAR role_name
        TEXT description
        JSONB permissions
        TIMESTAMP created_at
    }
    
    USER_ROLES {
        UUID user_id FK
        UUID role_id FK
        TIMESTAMP granted_at
    }
    
    TENANTS ||--o{ USERS : "拥有"
    TENANTS ||--o{ ROLES : "定义"
    USERS ||--o{ USER_ROLES : "分配"
    ROLES ||--o{ USER_ROLES : "包含"
```

---

## 三、CTMS 模块 ER 图

```mermaid
erDiagram
    TRIALS {
        UUID trial_id PK
        UUID tenant_id FK
        VARCHAR trial_code UK
        VARCHAR trial_name
        VARCHAR protocol_number
        VARCHAR sponsor_name
        VARCHAR phase
        VARCHAR therapeutic_area
        DATE start_date
        DATE end_date
        VARCHAR status
        DECIMAL budget
        UUID manager_id FK
        JSONB config
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    STUDY_SITES {
        UUID site_id PK
        UUID tenant_id FK
        UUID trial_id FK
        VARCHAR site_code
        VARCHAR site_name
        VARCHAR hospital_name
        TEXT address
        VARCHAR city
        VARCHAR province
        VARCHAR country
        VARCHAR contact_person
        VARCHAR contact_phone
        VARCHAR contact_email
        VARCHAR gcp_certificate
        DATE gcp_expiry
        UUID principal_investigator_id FK
        VARCHAR status
        INTEGER enrollment_target
        INTEGER enrolled_count
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    INVESTIGATORS {
        UUID investigator_id PK
        UUID tenant_id FK
        UUID site_id FK
        UUID user_id FK
        VARCHAR name
        VARCHAR title
        VARCHAR specialty
        VARCHAR qualification
        DATE gcp_certificate_date
        VARCHAR signature_image
        VARCHAR status
        TIMESTAMP created_at
    }
    
    ETMF_DOCUMENTS {
        UUID document_id PK
        UUID tenant_id FK
        UUID trial_id FK
        VARCHAR document_code
        VARCHAR document_name
        VARCHAR document_type
        VARCHAR category
        VARCHAR version
        VARCHAR status
        VARCHAR file_path
        BIGINT file_size
        VARCHAR file_type
        UUID uploader_id FK
        TIMESTAMP uploaded_at
        UUID approved_by FK
        TIMESTAMP approved_at
        TEXT approval_notes
        UUID parent_document_id FK
        TEXT version_notes
        JSONB metadata
    }
    
    WORK_HOURS {
        UUID work_hour_id PK
        UUID tenant_id FK
        UUID user_id FK
        UUID trial_id FK
        VARCHAR project_task
        DATE work_date
        DECIMAL hours
        VARCHAR work_type
        TEXT notes
        VARCHAR status
        UUID manager_id FK
        TIMESTAMP approved_at
        TEXT approval_notes
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    TRIALS ||--o{ STUDY_SITES : "包含"
    TRIALS ||--o{ ETMF_DOCUMENTS : "管理"
    TRIALS ||--o{ WORK_HOURS : "记录"
    TRIALS ||--o{ INVESTIGATORS : "指派"
    STUDY_SITES ||--o{ INVESTIGATORS : "雇佣"
    STUDY_SITES ||--o{ WORK_HOURS : "关联"
    ETMF_DOCUMENTS ||--o{ ETMF_DOCUMENTS : "父子关系"
    USERS ||--o{ INVESTIGATORS : "成为"
    USERS ||--o{ WORK_HOURS : "填报"
```

---

## 四、EDC 模块 ER 图

```mermaid
erDiagram
    CRF_FORMS {
        UUID form_id PK
        UUID tenant_id FK
        UUID trial_id FK
        VARCHAR form_code
        VARCHAR form_name
        VARCHAR form_version
        VARCHAR form_type
        TEXT description
        BOOLEAN is_active
        INTEGER display_order
        JSONB layout_config
        JSONB validation_rules
        JSONB cdash_mapping
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    CRF_FIELDS {
        UUID field_id PK
        UUID form_id FK
        VARCHAR field_code UK
        VARCHAR field_name
        VARCHAR field_type
        BOOLEAN required
        BOOLEAN readonly
        INTEGER max_length
        NUMERIC min_value
        NUMERIC max_value
        TEXT default_value
        JSONB options
        VARCHAR validation_pattern
        TEXT validation_message
        TEXT display_condition
        VARCHAR cdash_domain
        VARCHAR sdtm_variable
        TEXT help_text
        INTEGER display_order
        TIMESTAMP created_at
    }
    
    VISITS {
        UUID visit_id PK
        UUID tenant_id FK
        UUID trial_id FK
        VARCHAR visit_code
        VARCHAR visit_name
        INTEGER visit_day_min
        INTEGER visit_day_max
        INTEGER visit_duration_min
        INTEGER visit_duration_max
        BOOLEAN is_mandatory
        INTEGER display_order
        UUID[] form_ids
        TIMESTAMP created_at
    }
    
    SUBJECTS {
        UUID subject_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID site_id FK
        VARCHAR subject_code
        VARCHAR screen_fail_reason
        DATE screen_date
        DATE randomization_date
        VARCHAR randomization_num
        VARCHAR treatment_arm
        VARCHAR enrollment_status
        DATE withdrawal_date
        TEXT withdrawal_reason
        DATE date_of_birth
        VARCHAR gender
        VARCHAR ethnicity
        DECIMAL height
        DECIMAL weight
        DECIMAL bmi
        VARCHAR status
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    SUBJECT_VISITS {
        UUID visit_record_id PK
        UUID tenant_id FK
        UUID subject_id FK
        UUID visit_id FK
        DATE visit_date
        INTEGER actual_day
        VARCHAR status
        TEXT notes
        TIMESTAMP completed_at
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    FORM_DATA {
        UUID data_id PK
        UUID tenant_id FK
        UUID visit_record_id FK
        UUID form_id FK
        VARCHAR form_version
        JSONB data_json
        UUID submitter_id FK
        TIMESTAMP submitted_at
        VARCHAR status
        UUID reviewer_id FK
        TIMESTAMP reviewed_at
        VARCHAR review_status
        TEXT review_notes
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    QUERIES {
        UUID query_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID subject_id FK
        UUID visit_record_id FK
        UUID form_id FK
        VARCHAR field_code
        VARCHAR query_title
        TEXT query_description
        VARCHAR query_status
        VARCHAR priority
        UUID assigned_to FK
        UUID creator_id FK
        TIMESTAMP created_at
        TIMESTAMP resolved_at
        UUID resolved_by FK
        TEXT resolution_notes
        TEXT response_notes
    }
    
    AUDIT_TRAIL {
        UUID audit_id PK
        UUID tenant_id FK
        VARCHAR entity_type
        UUID entity_id
        VARCHAR action
        VARCHAR field_name
        JSONB old_value
        JSONB new_value
        UUID user_id FK
        VARCHAR ip_address
        TEXT user_agent
        TIMESTAMP created_at
    }
    
    CRF_FORMS ||--o{ CRF_FIELDS : "包含"
    CRF_FORMS ||--o{ FORM_DATA : "提交"
    TRIALS ||--o{ VISITS : "定义"
    TRIALS ||--o{ SUBJECTS : "管理"
    TRIALS ||--o{ QUERIES : "处理"
    TRIALS ||--o{ CRF_FORMS : "设计"
    STUDY_SITES ||--o{ SUBJECTS : "入组"
    SUBJECTS ||--o{ SUBJECT_VISITS : "访视"
    SUBJECTS ||--o{ QUERIES : "涉及"
    VISITS ||--o{ SUBJECT_VISITS : "安排"
    SUBJECT_VISITS ||--o{ FORM_DATA : "提交"
    SUBJECTS ||--o{ RANDOMIZATION_REQUESTS : "随机化"
```

---

## 五、SDTM 数据模型 ER 图

```mermaid
erDiagram
    SDTM_DM {
        UUID record_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID subject_id FK
        VARCHAR STUDYID
        VARCHAR USUBJID
        VARCHAR SUBJID
        VARCHAR RMSTCD
        VARCHAR RMSTRTCD
        VARCHAR ACTARMCD
        VARCHAR ACTARMLN
        VARCHAR COUNTRY
        VARCHAR STATE
        VARCHAR SITEID
        VARCHAR SITEONTR
        VARCHAR SEXF
        VARCHAR RACEF
        VARCHAR ETHNIC
        VARCHAR SPRTRTFL
        VARCHAR SPRTRT
        VARCHAR DTHFL
        DATE DTHDT
        TIMESTAMP created_at
    }
    
    SDTM_SCREEN {
        UUID record_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID subject_id FK
        VARCHAR STUDYID
        VARCHAR USUBJID
        VARCHAR SCREENF
        DATE SCREENDT
        VARCHAR SCREASFL
        VARCHAR SCRREASN
        TIMESTAMP created_at
    }
    
    SDTM_AE {
        UUID record_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID subject_id FK
        VARCHAR STUDYID
        VARCHAR USUBJID
        VARCHAR AESEQ
        VARCHAR AETERM
        VARCHAR AEDECOD
        VARCHAR AEBODSYS
        VARCHAR AESEV
        VARCHAR AEREL
        DATE AESTDTC
        DATE AEENDTC
        VARCHAR AEOUT
        VARCHAR AESER
        VARCHAR AECONTRT
        TIMESTAMP created_at
    }
    
    SDTM_LB {
        UUID record_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID subject_id FK
        VARCHAR STUDYID
        VARCHAR USUBJID
        VARCHAR LBOSEQ
        VARCHAR LBDOM
        VARCHAR LBCAT
        VARCHAR LBTESTCD
        VARCHAR LBTEST
        VARCHAR LBORRES
        VARCHAR LBORRESU
        VARCHAR LBNRLCD
        NUMERIC LBNRLO
        NUMERIC LBNRHI
        VARCHAR LBORNRFL
        VARCHAR LBSTRESC
        NUMERIC LBSTRESN
        VARCHAR LBSTRESU
        VARCHAR LBSPCA
        DATE LBDT
        TIMESTAMP created_at
    }
    
    SDTM_EX {
        UUID record_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID subject_id FK
        VARCHAR STUDYID
        VARCHAR USUBJID
        VARCHAR EXSEQ
        VARCHAR EXTRT
        VARCHAR EXTRTP
        NUMERIC EXDOSE
        VARCHAR EXDOSU
        VARCHAR EXDOSFRQ
        VARCHAR EXROUTE
        VARCHAR EXSTA
        VARCHAR EXEN
        DATE EXSTDTC
        DATE EXENDTC
        TIMESTAMP created_at
    }
    
    SDTM_DS {
        UUID record_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID subject_id FK
        VARCHAR STUDYID
        VARCHAR USUBJID
        VARCHAR DSSEQ
        VARCHAR DSCAT
        VARCHAR DSDECOD
        VARCHAR DSDOM
        VARCHAR DSTERM
        VARCHAR DSRSLT
        DATE DSSTDTC
        DATE DSENDTC
        TIMESTAMP created_at
    }
    
    TRIALS ||--o{ SDTM_DM : "生成"
    TRIALS ||--o{ SDTM_AE : "生成"
    TRIALS ||--o{ SDTM_LB : "生成"
    TRIALS ||--o{ SDTM_EX : "生成"
    TRIALS ||--o{ SDTM_DS : "生成"
    
    SUBJECTS ||--o{ SDTM_DM : "映射"
    SUBJECTS ||--o{ SDTM_AE : "映射"
    SUBJECTS ||--o{ SDTM_LB : "映射"
    SUBJECTS ||--o{ SDTM_EX : "映射"
    SUBJECTS ||--o{ SDTM_DS : "映射"
```

---

## 六、IWRS 模块 ER 图

```mermaid
erDiagram
    RANDOMIZATION_SCHEMES {
        UUID scheme_id PK
        UUID tenant_id FK
        UUID trial_id FK
        VARCHAR scheme_name
        VARCHAR scheme_type
        TEXT description
        JSONB treatment_arms
        INTEGER[] block_sizes
        JSONB stratification_factors
        JSONB minimization_params
        BOOLEAN is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    DRUG_CONFIGS {
        UUID drug_id PK
        UUID tenant_id FK
        UUID trial_id FK
        VARCHAR drug_code
        VARCHAR drug_name
        VARCHAR drug_type
        VARCHAR packaging
        TEXT storage_condition
        INTEGER expiry_days
        BOOLEAN is_active
        TIMESTAMP created_at
    }
    
    DRUG_INVENTORY {
        UUID inventory_id PK
        UUID tenant_id FK
        UUID drug_id FK
        UUID site_id FK
        VARCHAR batch_number
        INTEGER quantity
        DATE expiry_date
        VARCHAR status
        VARCHAR location
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    RANDOMIZATION_REQUESTS {
        UUID request_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID site_id FK
        UUID subject_id FK
        UUID scheme_id FK
        TIMESTAMP request_time
        UUID requested_by FK
        JSONB stratification_factors
        JSONB randomization_result
        VARCHAR treatment_arm
        VARCHAR randomization_num
        JSONB drug_allocation
        VARCHAR ip_address
        TIMESTAMP created_at
    }
    
    DRUG_ALLOCATIONS {
        UUID allocation_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID subject_id FK
        UUID site_id FK
        UUID randomization_request_id FK
        UUID drug_id FK
        VARCHAR drug_code
        VARCHAR batch_number
        INTEGER quantity
        DATE allocated_date
        UUID allocated_by FK
        VARCHAR delivery_status
        DATE delivery_date
        INTEGER returned_quantity
        INTEGER destroyed_quantity
        TIMESTAMP created_at
    }
    
    TRIALS ||--o{ RANDOMIZATION_SCHEMES : "配置"
    TRIALS ||--o{ DRUG_CONFIGS : "管理"
    TRIALS ||--o{ RANDOMIZATION_REQUESTS : "请求"
    TRIALS ||--o{ DRUG_ALLOCATIONS : "分配"
    
    STUDY_SITES ||--o{ DRUG_INVENTORY : "存储"
    STUDY_SITES ||--o{ RANDOMIZATION_REQUESTS : "发起"
    
    SUBJECTS ||--o{ RANDOMIZATION_REQUESTS : "随机化"
    SUBJECTS ||--o{ DRUG_ALLOCATIONS : "接受"
    
    RANDOMIZATION_SCHEMES ||--o{ RANDOMIZATION_REQUESTS : "执行"
    DRUG_CONFIGS ||--o{ DRUG_INVENTORY : "配置"
    DRUG_CONFIGS ||--o{ DRUG_ALLOCATIONS : "分配"
    
    USERS ||--o{ RANDOMIZATION_REQUESTS : "请求"
    USERS ||--o{ DRUG_ALLOCATIONS : "分配"
```

---

## 七、医生病历夹模块 ER 图

```mermaid
erDiagram
    PATIENT_CLINICAL_RECORDS {
        UUID record_id PK
        UUID tenant_id FK
        UUID doctor_id FK
        VARCHAR patient_external_id
        VARCHAR patient_name
        VARCHAR patient_id_card
        VARCHAR gender
        DATE date_of_birth
        VARCHAR phone
        TEXT address
        TEXT medical_history
        TEXT allergy_history
        TEXT family_history
        VARCHAR status
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    PATIENT_FORMS {
        UUID form_id PK
        UUID tenant_id FK
        UUID doctor_id FK
        VARCHAR form_name
        VARCHAR form_code UK
        UUID source_crf_form_id FK
        BOOLEAN is_active
        JSONB fields_config
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    PATIENT_FORM_DATA {
        UUID data_id PK
        UUID tenant_id FK
        UUID patient_record_id FK
        UUID form_id FK
        VARCHAR form_version
        DATE visit_date
        JSONB data_json
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    LAB_RESULTS {
        UUID result_id PK
        UUID tenant_id FK
        UUID patient_record_id FK
        DATE result_date
        VARCHAR test_name
        VARCHAR test_code
        VARCHAR result_value
        VARCHAR result_unit
        NUMERIC result_numeric
        VARCHAR normal_range
        VARCHAR abnormal_flag
        VARCHAR test_type
        VARCHAR facility_name
        VARCHAR document_path
        TIMESTAMP created_at
    }
    
    IMAGING_RESULTS {
        UUID imaging_id PK
        UUID tenant_id FK
        UUID patient_record_id FK
        DATE imaging_date
        VARCHAR imaging_type
        VARCHAR body_part
        TEXT finding
        TEXT impression
        VARCHAR report_document
        JSONB image_urls
        VARCHAR facility_name
        TIMESTAMP created_at
    }
    
    PRESCRIPTIONS {
        UUID prescription_id PK
        UUID tenant_id FK
        UUID patient_record_id FK
        DATE prescription_date
        UUID doctor_id FK
        VARCHAR drug_name
        VARCHAR drug_code
        VARCHAR dosage
        VARCHAR frequency
        VARCHAR duration
        VARCHAR administration_route
        TEXT instructions
        VARCHAR prescription_type
        BOOLEAN is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    USERS ||--o{ PATIENT_CLINICAL_RECORDS : "管理"
    USERS ||--o{ PATIENT_FORMS : "设计"
    USERS ||--o{ PRESCRIPTIONS : "开具"
    
    PATIENT_CLINICAL_RECORDS ||--o{ PATIENT_FORMS : "拥有"
    PATIENT_CLINICAL_RECORDS ||--o{ PATIENT_FORM_DATA : "记录"
    PATIENT_CLINICAL_RECORDS ||--o{ LAB_RESULTS : "包含"
    PATIENT_CLINICAL_RECORDS ||--o{ IMAGING_RESULTS : "包含"
    PATIENT_CLINICAL_RECORDS ||--o{ PRESCRIPTIONS : "接受"
    
    CRF_FORMS ||--o{ PATIENT_FORMS : "引用"
```

---

## 八、数据验证与审计 ER 图

```mermaid
erDiagram
    DATA_VALIDATION_RULES {
        UUID rule_id PK
        UUID tenant_id FK
        UUID trial_id FK
        VARCHAR rule_name
        VARCHAR rule_type
        VARCHAR target_entity
        VARCHAR target_table
        TEXT rule_definition
        INTEGER priority
        VARCHAR status
        JSONB configuration
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    DATA_VALIDATION_RESULTS {
        UUID result_id PK
        UUID rule_id FK
        UUID tenant_id FK
        UUID trial_id FK
        UUID entity_id
        VARCHAR entity_type
        VARCHAR result_status
        TEXT error_message
        JSONB error_details
        UUID validated_by FK
        TIMESTAMP validated_at
    }
    
    AUDIT_TRAIL {
        UUID audit_id PK
        UUID tenant_id FK
        VARCHAR entity_type
        UUID entity_id
        VARCHAR action
        VARCHAR field_name
        JSONB old_value
        JSONB new_value
        UUID user_id FK
        VARCHAR ip_address
        TEXT user_agent
        TIMESTAMP created_at
    }
    
    NOTIFICATIONS {
        UUID notification_id PK
        UUID tenant_id FK
        UUID user_id FK
        VARCHAR notification_type
        VARCHAR title
        TEXT content
        UUID related_entity_id
        VARCHAR related_entity_type
        BOOLEAN is_read
        TIMESTAMP created_at
        TIMESTAMP read_at
    }
    
    DATA_EXPORTS {
        UUID export_id PK
        UUID tenant_id FK
        UUID trial_id FK
        UUID created_by FK
        VARCHAR export_type
        VARCHAR export_format
        VARCHAR status
        VARCHAR file_path
        BIGINT file_size
        TIMESTAMP created_at
        TIMESTAMP completed_at
    }
    
    TENANTS ||--o{ DATA_VALIDATION_RULES : "定义"
    TENANTS ||--o{ AUDIT_TRAIL : "审计"
    TENANTS ||--o{ NOTIFICATIONS : "发送"
    TENANTS ||--o{ DATA_EXPORTS : "导出"
    
    TRIALS ||--o{ DATA_VALIDATION_RULES : "配置"
    TRIALS ||--o{ DATA_VALIDATION_RESULTS : "生成"
    TRIALS ||--o{ DATA_EXPORTS : "导出"
    
    USERS ||--o{ DATA_VALIDATION_RESULTS : "验证"
    USERS ||--o{ NOTIFICATIONS : "接收"
    USERS ||--o{ DATA_EXPORTS : "创建"
    USERS ||--o{ AUDIT_TRAIL : "操作"
    
    DATA_VALIDATION_RULES ||--o{ DATA_VALIDATION_RESULTS : "触发"
```

---

## 九、数据库关系详细说明

### 9.1 租户隔离策略

```mermaid
graph LR
    A[租户表 TENANTS] --> B[用户表 USERS]
    A --> C[试验表 TRIALS]
    A --> D[表单表 CRF_FORMS]
    A --> E[患者表 SUBJECTS]
    A --> F[审计表 AUDIT_TRAIL]
    
    B --> G[工时表 WORK_HOURS]
    B --> H[角色表 USER_ROLES]
    
    C --> I[研究中心表 STUDY_SITES]
    C --> J[访视表 VISITS]
    C --> K[eCRF 表单表 CRF_FORMS]
    
    I --> L[研究者表 INVESTIGATORS]
    I --> M[药物库存表 DRUG_INVENTORY]
    
    K --> N[字段定义表 CRF_FIELDS]
    K --> O[表单数据表 FORM_DATA]
```

**租户隔离机制:**
1. **Schema 隔离**: 每个租户独立的 PostgreSQL Schema
2. **行级安全**: 所有业务表包含 `tenant_id` 字段
3. **查询过滤**: 所有查询自动过滤 `tenant_id`
4. **权限控制**: 租户间数据完全隔离

### 9.2 核心业务流程 ER 关系

```mermaid
graph TB
    A[创建试验 TRIALS] --> B[设计表单 CRF_FORMS]
    A --> C[设置访视 VISITS]
    A --> D[配置随机化 RANDOMIZATION_SCHEMES]
    
    B --> E[拖拽字段 CRF_FIELDS]
    B --> F[设置验证规则]
    B --> G[映射 CDASH]
    
    C --> H[添加访视计划]
    C --> I[设置访视窗口]
    
    D --> J[配置治疗组]
    D --> K[设置随机化方法]
    
    A --> L[入组患者 SUBJECTS]
    L --> M[创建访视 SUBJECT_VISITS]
    M --> N[提交表单 FORM_DATA]
    
    N --> O[数据验证]
    N --> P[生成疑问 QUERIES]
    
    L --> Q[随机化分配 RANDOMIZATION_REQUESTS]
    Q --> R[药物分配 DRUG_ALLOCATIONS]
    
    N --> S[生成 SDTM 数据]
    S --> T[DM 域]
    S --> U[AE 域]
    S --> V[LB 域]
    S --> W[EX 域]
```

---

## 十、索引优化设计

```sql
-- 租户隔离索引
CREATE INDEX idx_tenant_all ON tenants(tenant_id);
CREATE INDEX idx_subjects_tenant ON subjects(tenant_id);
CREATE INDEX idx_forms_tenant ON crf_forms(tenant_id);
CREATE INDEX idx_data_tenant ON form_data(tenant_id);
CREATE INDEX idx_audit_tenant ON audit_trail(tenant_id);

-- 查询性能索引
CREATE INDEX idx_subjects_trial ON subjects(trial_id);
CREATE INDEX idx_subjects_site ON subjects(site_id);
CREATE INDEX idx_subject_visits_subject ON subject_visits(subject_id);
CREATE INDEX idx_form_data_visit ON form_data(visit_record_id);
CREATE INDEX idx_form_data_form ON form_data(form_id);
CREATE INDEX idx_visits_trial ON visits(trial_id);
CREATE INDEX idx_schemes_trial ON randomization_schemes(trial_id);
CREATE INDEX idx_requests_subject ON randomization_requests(subject_id);

-- SDTM 数据索引
CREATE INDEX idx_sdtm_dm_trial ON sdtm_dm(trial_id, subject_id);
CREATE INDEX idx_sdtm_ae_trial ON sdtm_ae(trial_id, subject_id);
CREATE INDEX idx_sdtm_lb_trial ON sdtm_lb(trial_id, subject_id);
CREATE INDEX idx_sdtm_ex_trial ON sdtm_ex(trial_id, subject_id);
CREATE INDEX idx_sdtm_ds_trial ON sdtm_ds(trial_id, subject_id);

-- 全文搜索索引
CREATE INDEX idx_trial_name ON trials USING gin(to_tsvector('chinese', trial_name));
CREATE INDEX idx_site_name ON study_sites USING gin(to_tsvector('chinese', site_name));
CREATE INDEX idx_patient_name ON patient_clinical_records USING gin(to_tsvector('chinese', patient_name));

-- 复合索引
CREATE INDEX idx_subject_trial_site ON subjects(trial_id, site_id, status);
CREATE INDEX idx_form_data_status ON form_data(status, updated_at);
CREATE INDEX idx_queries_status ON queries(status, created_at);
CREATE INDEX idx_work_hours_date ON work_hours(work_date, user_id);
```

---

## 十一、数据备份与归档策略

```mermaid
graph LR
    A[生产数据库] --> B[主从复制]
    B --> C[从库 1]
    B --> D[从库 2]
    
    C --> E[每日快照备份]
    D --> F[每小时增量备份]
    
    E --> G[云存储备份]
    F --> H[本地备份]
    
    G --> I[归档存储]
    H --> I
    
    I --> J[灾难恢复]
```

**备份策略:**
- **实时**: 主从复制
- **每小时**: 增量备份
- **每日**: 全量备份
- **每月**: 归档到冷存储
- **保留期**: 生产数据 7 年（符合 GCP 要求）

---

## 十二、ER 图图例说明

```
实体表示:
┌─────────────────┐
│ 表名             │
├─────────────────┤
│ 字段 1           │
│ 字段 2           │
│ ...              │
└─────────────────┘

关系表示:
1:N - 一对多关系
1:1 - 一对一关系
M:N - 多对多关系 (通过关联表)
self-referencing - 自引用关系
```

---

*文档版本：v1.0*
*创建日期：2026 年*
*维护人：蔡宇恒*
