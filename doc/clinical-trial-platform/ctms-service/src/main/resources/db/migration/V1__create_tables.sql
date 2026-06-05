-- CTMS 服务数据库初始化脚本
-- 表：试验主表
CREATE TABLE IF NOT EXISTS trial (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protocol_id VARCHAR(100) NOT NULL UNIQUE,
    trial_name_en VARCHAR(500) NOT NULL,
    trial_name_cn VARCHAR(500),
    phase VARCHAR(20) NOT NULL,
    design_type VARCHAR(50),
    indication_area VARCHAR(500),
    trial_type VARCHAR(50),
    sponsor_name VARCHAR(500),
    cro_name VARCHAR(500),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'PLANNING',
    budget DECIMAL(18,2),
    actual_cost DECIMAL(18,2) DEFAULT 0,
    enrollment_target INTEGER DEFAULT 0,
    enrollment_actual INTEGER DEFAULT 0,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- 表：研究中心信息
CREATE TABLE IF NOT EXISTS study_site (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trial(id) ON DELETE CASCADE,
    site_id VARCHAR(50) NOT NULL,
    site_name_en VARCHAR(500) NOT NULL,
    site_name_cn VARCHAR(500),
    site_type VARCHAR(100),
    address_detail JSONB,
    contact_person VARCHAR(100),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(200),
    department VARCHAR(200),
    pi_name VARCHAR(100),
    pi_title VARCHAR(100),
    pi_email VARCHAR(200),
    crc_name VARCHAR(100),
    crc_email VARCHAR(200),
    gcp_certificate_number VARCHAR(100),
    gcp_expiry_date DATE,
    ethics_approval_number VARCHAR(100),
    ethics_approval_date DATE,
    site_status VARCHAR(50) DEFAULT 'SCREENING',
    enrollment_status VARCHAR(50) DEFAULT 'NOT_STARTED',
    enrollment_target INTEGER DEFAULT 0,
    enrollment_actual INTEGER DEFAULT 0,
    activation_date DATE,
    closure_date DATE,
    site_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    UNIQUE(trial_id, site_id)
);

-- 表：研究团队成员
CREATE TABLE IF NOT EXISTS study_site_member (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES study_site(id) ON DELETE CASCADE,
    member_name VARCHAR(100) NOT NULL,
    member_role VARCHAR(100) NOT NULL,
    member_title VARCHAR(100),
    member_email VARCHAR(200),
    member_phone VARCHAR(50),
    organization VARCHAR(200),
    qualification_documents JSONB,
    authorization_date DATE,
    authorization_expiry DATE,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 表：里程碑管理
CREATE TABLE IF NOT EXISTS trial_milestone (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trial(id) ON DELETE CASCADE,
    milestone_name VARCHAR(200) NOT NULL,
    milestone_type VARCHAR(50) NOT NULL,
    planned_date DATE NOT NULL,
    actual_date DATE,
    status VARCHAR(50) DEFAULT 'PLANNED',
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    description TEXT,
    responsible_person VARCHAR(100),
    actual_duration INTEGER,
    lag INTEGER,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 表：文档管理
CREATE TABLE IF NOT EXISTS document (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trial(id) ON DELETE CASCADE,
    document_name VARCHAR(500) NOT NULL,
    document_code VARCHAR(100),
    it_chapter VARCHAR(50),
    document_type VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    version VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'DRAFT',
    file_path VARCHAR(1000),
    file_size BIGINT,
    file_type VARCHAR(50),
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    description TEXT,
    tags JSONB,
    access_level VARCHAR(50) DEFAULT 'INTERNAL',
    retention_period INTEGER,
    archive_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 表：文档版本历史
CREATE TABLE IF NOT EXISTS document_version (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),
    version_notes TEXT,
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, version)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_trial_protocol ON trial(protocol_id);
CREATE INDEX IF NOT EXISTS idx_trial_status ON trial(status);
CREATE INDEX IF NOT EXISTS idx_study_site_trial ON study_site(trial_id);
CREATE INDEX IF NOT EXISTS idx_study_site_status ON study_site(site_status);
CREATE INDEX IF NOT EXISTS idx_document_trial ON document(trial_id);
CREATE INDEX IF NOT EXISTS idx_document_type ON document(document_type);
CREATE INDEX IF NOT EXISTS idx_milestone_trial ON trial_milestone(trial_id);
CREATE INDEX IF NOT EXISTS idx_milestone_status ON trial_milestone(status);

-- 注释
COMMENT ON TABLE trial IS '试验主表';
COMMENT ON TABLE study_site IS '研究中心信息表';
COMMENT ON TABLE study_site_member IS '研究团队成员表';
COMMENT ON TABLE trial_milestone IS '里程碑管理表';
COMMENT ON TABLE document IS '文档管理表';
COMMENT ON TABLE document_version IS '文档版本历史表';
