-- IWRS 服务数据库初始化脚本
-- 表：药物库存管理
CREATE TABLE IF NOT EXISTS drug_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    drug_code VARCHAR(100) NOT NULL,
    drug_name VARCHAR(500) NOT NULL,
    batch_number VARCHAR(100),
    dosage_form VARCHAR(100),
    strength VARCHAR(50),
    package_size INTEGER,
    unit_of_measure VARCHAR(20),
    quantity_on_hand INTEGER DEFAULT 0,
    quantity_reserved INTEGER DEFAULT 0,
    quantity_available INTEGER GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    location_description VARCHAR(500),
    storage_condition VARCHAR(200),
    manufacturing_date DATE,
    expiry_date DATE,
    status VARCHAR(50) DEFAULT 'AVAILABLE',
    last_stocktake_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    UNIQUE(trial_id, site_id, drug_code)
);

-- 表：药物发放记录
CREATE TABLE IF NOT EXISTS drug_shipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    shipment_number VARCHAR(100) NOT NULL UNIQUE,
    shipment_type VARCHAR(50),
    shipment_date DATE NOT NULL,
    received_date DATE,
    drug_items JSONB NOT NULL,
    shipping_method VARCHAR(100),
    tracking_number VARCHAR(200),
    carrier VARCHAR(100),
    temperature_controlled BOOLEAN DEFAULT FALSE,
    temperature_log JSONB,
    signed_by VARCHAR(100),
    signature_date TIMESTAMP,
    condition_on_arrival VARCHAR(100),
    remarks TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- 表：随机化日志
CREATE TABLE IF NOT EXISTS randomization_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    subject_id VARCHAR(50) NOT NULL,
    site_subject_id VARCHAR(50),
    randomization_number VARCHAR(100) NOT NULL UNIQUE,
    treatment_code VARCHAR(50) NOT NULL,
    treatment_arm VARCHAR(100) NOT NULL,
    block_id VARCHAR(50),
    stratification_factors JSONB,
    randomization_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    randomization_method VARCHAR(50),
    randomized_by VARCHAR(100),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    unblinding_requested BOOLEAN DEFAULT FALSE,
    unblinding_date TIMESTAMP,
    unblinding_reason TEXT,
    unblinded_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trial_id, subject_id)
);

-- 表：药物调整记录
CREATE TABLE IF NOT EXISTS drug_adjustment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    drug_inventory_id UUID,
    adjustment_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    previous_quantity INTEGER NOT NULL,
    new_quantity INTEGER NOT NULL,
    adjustment_reason VARCHAR(500),
    adjustment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adjusted_by VARCHAR(100) NOT NULL,
    approved_by VARCHAR(100),
    approved_date TIMESTAMP,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 表：药物回收记录
CREATE TABLE IF NOT EXISTS drug_return (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    shipment_id UUID,
    return_items JSONB NOT NULL,
    return_date DATE NOT NULL,
    return_reason VARCHAR(500),
    shipping_method VARCHAR(100),
    tracking_number VARCHAR(200),
    carrier VARCHAR(100),
    temperature_controlled BOOLEAN DEFAULT FALSE,
    received_by VARCHAR(100),
    received_date DATE,
    verification_status VARCHAR(50) DEFAULT 'PENDING',
    verification_notes TEXT,
    disposal_method VARCHAR(100),
    disposal_date DATE,
    disposal_certificate VARCHAR(200),
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_drug_inventory_trial ON drug_inventory(trial_id, site_id);
CREATE INDEX IF NOT EXISTS idx_drug_inventory_status ON drug_inventory(status);
CREATE INDEX IF NOT EXISTS idx_drug_shipment_site ON drug_shipment(trial_id, site_id);
CREATE INDEX IF NOT EXISTS idx_drug_shipment_status ON drug_shipment(status);
CREATE INDEX IF NOT EXISTS idx_randomization_trial ON randomization_log(trial_id, site_id);
CREATE INDEX IF NOT EXISTS idx_randomization_subject ON randomization_log(subject_id);
CREATE INDEX IF NOT EXISTS idx_drug_adjustment_site ON drug_adjustment(trial_id, site_id);
CREATE INDEX IF NOT EXISTS idx_drug_return_site ON drug_return(trial_id, site_id);

-- 注释
COMMENT ON TABLE drug_inventory IS '药物库存管理表';
COMMENT ON TABLE drug_shipment IS '药物发放记录表';
COMMENT ON TABLE randomization_log IS '随机化日志表';
COMMENT ON TABLE drug_adjustment IS '药物调整记录表';
COMMENT ON TABLE drug_return IS '药物回收记录表';
