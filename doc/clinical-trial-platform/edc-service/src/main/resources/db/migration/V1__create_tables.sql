-- EDC 服务数据库初始化脚本
-- 表：EDC 表单定义
CREATE TABLE IF NOT EXISTS crf (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crf_code VARCHAR(50) NOT NULL UNIQUE,
    crf_name VARCHAR(200) NOT NULL,
    crf_name_cn VARCHAR(200),
    protocol_id VARCHAR(100) NOT NULL,
    form_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'DRAFT',
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    schema_config JSONB,
    validation_rules JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- 表：EDC 表单字段定义
CREATE TABLE IF NOT EXISTS crf_form (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crf_id UUID NOT NULL REFERENCES crf(id) ON DELETE CASCADE,
    form_name VARCHAR(200) NOT NULL,
    form_code VARCHAR(100) NOT NULL,
    form_type VARCHAR(50) NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_section BOOLEAN DEFAULT FALSE,
    parent_form_id UUID REFERENCES crf_form(id),
    field_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 表：数据采集记录
CREATE TABLE IF NOT EXISTS data_entry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_site_id UUID NOT NULL,
    subject_id VARCHAR(50) NOT NULL,
    visit_code VARCHAR(50) NOT NULL,
    crf_id UUID NOT NULL REFERENCES crf(id),
    data_value JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'IN_PROGRESS',
    data_entry_user_id VARCHAR(100) NOT NULL,
    data_entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    edit_time TIMESTAMP,
    edit_user_id VARCHAR(100),
    edit_reason TEXT,
    is_locked BOOLEAN DEFAULT FALSE,
    locked_by VARCHAR(100),
    locked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trial_site_id, subject_id, crf_id, visit_code)
);

-- 表：数据疑问管理
CREATE TABLE IF NOT EXISTS query (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_entry_id UUID NOT NULL REFERENCES data_entry(id) ON DELETE CASCADE,
    query_title VARCHAR(500) NOT NULL,
    query_description TEXT,
    query_field_path VARCHAR(500),
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(20) DEFAULT 'OPEN',
    assigned_to VARCHAR(100),
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    response TEXT,
    response_time TIMESTAMP,
    is_resolved_by_editor BOOLEAN DEFAULT FALSE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_data_entry_subject ON data_entry(trial_site_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_data_entry_visit ON data_entry(trial_site_id, visit_code);
CREATE INDEX IF NOT EXISTS idx_data_entry_status ON data_entry(status);
CREATE INDEX IF NOT EXISTS idx_query_status ON query(status);
CREATE INDEX IF NOT EXISTS idx_query_data_entry ON query(data_entry_id);

-- 注释
COMMENT ON TABLE crf IS 'EDC 表单定义表';
COMMENT ON TABLE crf_form IS 'EDC 表单字段定义表';
COMMENT ON TABLE data_entry IS '数据采集记录表';
COMMENT ON TABLE query IS '数据疑问管理表';
