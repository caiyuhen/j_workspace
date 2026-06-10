-- ============================================
-- 中医数据要素系统 - 初始数据库脚本
-- 版本: V1.0.0
-- 日期: 2024-12-10
-- ============================================

-- 创建数据库（如不存在）
CREATE DATABASE IF NOT EXISTS tcm_data 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE tcm_data;

-- ============================================
-- 1. 用户与权限模块
-- ============================================

-- 组织机构表
CREATE TABLE sys_organization (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父机构ID',
    org_code VARCHAR(64) NOT NULL COMMENT '机构编码',
    org_name VARCHAR(128) NOT NULL COMMENT '机构名称',
    org_type VARCHAR(32) NOT NULL COMMENT '机构类型: HOSPITAL-医院, CLINIC-诊所, RESEARCH-科研, ENTERPRISE-企业, GOVERNMENT-政府',
    level INT DEFAULT 1 COMMENT '机构层级: 1-省级, 2-市级, 3-县级, 4-机构',
    province VARCHAR(64) COMMENT '省份',
    city VARCHAR(64) COMMENT '城市',
    district VARCHAR(64) COMMENT '区县',
    address VARCHAR(256) COMMENT '详细地址',
    contact_person VARCHAR(64) COMMENT '联系人',
    contact_phone VARCHAR(32) COMMENT '联系电话',
    license_no VARCHAR(128) COMMENT '执业许可证号',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-禁用, 1-启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_by BIGINT COMMENT '创建人',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT COMMENT '更新人',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '删除标记: 0-未删除, 1-已删除',
    UNIQUE KEY uk_org_code (org_code),
    KEY idx_parent_id (parent_id),
    KEY idx_org_type (org_type),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织机构表';

-- 用户表
CREATE TABLE sys_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    username VARCHAR(64) NOT NULL COMMENT '用户名',
    password VARCHAR(256) NOT NULL COMMENT '密码',
    real_name VARCHAR(64) COMMENT '真实姓名',
    phone VARCHAR(32) COMMENT '手机号',
    email VARCHAR(128) COMMENT '邮箱',
    avatar VARCHAR(256) COMMENT '头像URL',
    org_id BIGINT COMMENT '所属机构ID',
    dept_id BIGINT COMMENT '所属部门ID',
    title VARCHAR(64) COMMENT '职称',
    specialty VARCHAR(256) COMMENT '专业领域',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-禁用, 1-启用, 2-锁定',
    last_login_time DATETIME COMMENT '最后登录时间',
    last_login_ip VARCHAR(64) COMMENT '最后登录IP',
    login_fail_count INT DEFAULT 0 COMMENT '登录失败次数',
    created_by BIGINT COMMENT '创建人',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT COMMENT '更新人',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '删除标记',
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_phone (phone),
    KEY idx_org_id (org_id),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 角色表
CREATE TABLE sys_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    role_code VARCHAR(64) NOT NULL COMMENT '角色编码',
    role_name VARCHAR(128) NOT NULL COMMENT '角色名称',
    role_type VARCHAR(32) DEFAULT 'CUSTOM' COMMENT '角色类型: SYSTEM-系统预设, CUSTOM-自定义',
    description VARCHAR(256) COMMENT '描述',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-禁用, 1-启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_by BIGINT COMMENT '创建人',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by BIGINT COMMENT '更新人',
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '删除标记',
    UNIQUE KEY uk_role_code (role_code),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- 用户角色关联表
CREATE TABLE sys_user_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_role (user_id, role_id),
    KEY idx_user_id (user_id),
    KEY idx_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- 权限表
CREATE TABLE sys_permission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父权限ID',
    perm_code VARCHAR(128) NOT NULL COMMENT '权限编码',
    perm_name VARCHAR(128) NOT NULL COMMENT '权限名称',
    perm_type VARCHAR(32) NOT NULL COMMENT '权限类型: MENU-菜单, BUTTON-按钮, API-接口, DATA-数据',
    path VARCHAR(256) COMMENT '路由路径/API路径',
    component VARCHAR(128) COMMENT '前端组件',
    icon VARCHAR(64) COMMENT '图标',
    method VARCHAR(16) COMMENT '请求方法: GET/POST/PUT/DELETE',
    status TINYINT DEFAULT 1 COMMENT '状态',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_perm_code (perm_code),
    KEY idx_parent_id (parent_id),
    KEY idx_perm_type (perm_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- 角色权限关联表
CREATE TABLE sys_role_permission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_id BIGINT NOT NULL COMMENT '角色ID',
    permission_id BIGINT NOT NULL COMMENT '权限ID',
    data_scope VARCHAR(32) DEFAULT 'ALL' COMMENT '数据范围: ALL-全部, ORG-本机构, DEPT-本部门, SELF-本人',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_role_perm (role_id, permission_id),
    KEY idx_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- ============================================
-- 2. 数据标准规范模块
-- ============================================

-- 数据标准分类表
CREATE TABLE data_standard_category (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    parent_id BIGINT DEFAULT 0 COMMENT '父分类ID',
    category_code VARCHAR(64) NOT NULL COMMENT '分类编码',
    category_name VARCHAR(128) NOT NULL COMMENT '分类名称',
    category_type VARCHAR(32) NOT NULL COMMENT '分类类型: TERMINOLOGY-术语, CODING-编码, CLASSIFICATION-分类, METADATA-元数据',
    description TEXT COMMENT '描述',
    status TINYINT DEFAULT 1 COMMENT '状态',
    sort_order INT DEFAULT 0,
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_category_code (category_code),
    KEY idx_parent_id (parent_id),
    KEY idx_type (category_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据标准分类表';

-- 数据标准表
CREATE TABLE data_standard (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category_id BIGINT NOT NULL COMMENT '分类ID',
    standard_code VARCHAR(128) NOT NULL COMMENT '标准编码',
    standard_name VARCHAR(256) NOT NULL COMMENT '标准名称',
    standard_alias VARCHAR(256) COMMENT '标准别名',
    standard_type VARCHAR(32) NOT NULL COMMENT '标准类型',
    definition TEXT COMMENT '定义',
    data_type VARCHAR(32) COMMENT '数据类型',
    data_length INT COMMENT '数据长度',
    data_format VARCHAR(64) COMMENT '数据格式',
    allowed_values TEXT COMMENT '允许值列表(JSON)',
    reference_source VARCHAR(256) COMMENT '参考来源',
    version VARCHAR(32) DEFAULT '1.0' COMMENT '版本号',
    status VARCHAR(16) DEFAULT 'DRAFT' COMMENT '状态: DRAFT-草稿, PUBLISHED-已发布, DEPRECATED-已废止',
    publish_time DATETIME COMMENT '发布时间',
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_standard_code (standard_code),
    KEY idx_category_id (category_id),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据标准表';

-- ============================================
-- 3. 数据分类分级模块
-- ============================================

-- 数据分类表
CREATE TABLE data_classification (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    parent_id BIGINT DEFAULT 0 COMMENT '父分类ID',
    class_code VARCHAR(64) NOT NULL COMMENT '分类编码',
    class_name VARCHAR(128) NOT NULL COMMENT '分类名称',
    class_type VARCHAR(32) NOT NULL COMMENT '分类类型: BUSINESS-业务领域, DATA_TYPE-数据类型',
    description TEXT COMMENT '描述',
    level INT DEFAULT 1 COMMENT '层级',
    status TINYINT DEFAULT 1,
    sort_order INT DEFAULT 0,
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_class_code (class_code),
    KEY idx_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据分类表';

-- 数据分级表
CREATE TABLE data_classification_level (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    level_code VARCHAR(16) NOT NULL COMMENT '级别编码: L1/L2/L3/L4',
    level_name VARCHAR(64) NOT NULL COMMENT '级别名称',
    level_desc TEXT COMMENT '级别描述',
    color VARCHAR(16) COMMENT '标识颜色',
    access_control TEXT COMMENT '访问控制策略(JSON)',
    storage_policy TEXT COMMENT '存储策略(JSON)',
    circulation_policy TEXT COMMENT '流通策略(JSON)',
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_level_code (level_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据分级表';

-- 数据资产分类分级关联表
CREATE TABLE data_asset_classification (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asset_id BIGINT NOT NULL COMMENT '资产ID',
    class_id BIGINT NOT NULL COMMENT '分类ID',
    level_id BIGINT NOT NULL COMMENT '分级ID',
    auto_classified TINYINT DEFAULT 0 COMMENT '是否自动分类: 0-人工, 1-自动',
    confidence_score DECIMAL(5,2) COMMENT '自动分类置信度',
    classified_by BIGINT COMMENT '分类人',
    classified_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_asset_class (asset_id, class_id),
    KEY idx_asset_id (asset_id),
    KEY idx_level_id (level_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据资产分类分级关联表';

-- ============================================
-- 4. 元数据管理模块
-- ============================================

-- 数据源表
CREATE TABLE meta_data_source (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_code VARCHAR(64) NOT NULL COMMENT '数据源编码',
    source_name VARCHAR(128) NOT NULL COMMENT '数据源名称',
    source_type VARCHAR(32) NOT NULL COMMENT '数据源类型: MYSQL, ORACLE, POSTGRESQL, HIVE, API, FILE',
    connection_info TEXT COMMENT '连接信息(JSON加密存储)',
    description TEXT COMMENT '描述',
    org_id BIGINT COMMENT '所属机构ID',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-禁用, 1-启用',
    last_sync_time DATETIME COMMENT '最后同步时间',
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_source_code (source_code),
    KEY idx_org_id (org_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据源表';

-- 元数据表（数据库/表/字段）
CREATE TABLE meta_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_id BIGINT NOT NULL COMMENT '数据源ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父元数据ID',
    meta_code VARCHAR(256) NOT NULL COMMENT '元数据编码(库名.表名.字段名)',
    meta_name VARCHAR(256) NOT NULL COMMENT '元数据名称',
    meta_type VARCHAR(32) NOT NULL COMMENT '元数据类型: DATABASE, TABLE, COLUMN, VIEW, INDEX',
    meta_path VARCHAR(512) COMMENT '完整路径',
    data_type VARCHAR(64) COMMENT '数据类型',
    data_length INT COMMENT '数据长度',
    is_nullable TINYINT DEFAULT 1 COMMENT '是否可为空',
    default_value VARCHAR(256) COMMENT '默认值',
    description TEXT COMMENT '描述/注释',
    business_desc TEXT COMMENT '业务描述',
    owner_id BIGINT COMMENT '负责人ID',
    status TINYINT DEFAULT 1,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_source_meta (source_id, meta_code),
    KEY idx_source_id (source_id),
    KEY idx_parent_id (parent_id),
    KEY idx_meta_type (meta_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='元数据表';

-- 数据血缘表
CREATE TABLE meta_data_lineage (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_meta_id BIGINT NOT NULL COMMENT '源元数据ID',
    target_meta_id BIGINT NOT NULL COMMENT '目标元数据ID',
    lineage_type VARCHAR(32) NOT NULL COMMENT '血缘类型: ETL, QUERY, API, MANUAL',
    lineage_detail TEXT COMMENT '血缘详情(转换逻辑等)',
    job_name VARCHAR(128) COMMENT '作业名称',
    job_id VARCHAR(64) COMMENT '作业ID',
    confidence DECIMAL(3,2) DEFAULT 1.00 COMMENT '置信度',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_lineage (source_meta_id, target_meta_id, lineage_type),
    KEY idx_source (source_meta_id),
    KEY idx_target (target_meta_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据血缘表';

-- ============================================
-- 5. 主数据管理模块
-- ============================================

-- 主数据模型表
CREATE TABLE master_data_model (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    model_code VARCHAR(64) NOT NULL COMMENT '模型编码',
    model_name VARCHAR(128) NOT NULL COMMENT '模型名称',
    model_type VARCHAR(32) NOT NULL COMMENT '模型类型: PATIENT-患者, DOCTOR-医师, HERB-药材, FORMULA-方剂, DISEASE-病证',
    description TEXT COMMENT '描述',
    fields_schema TEXT COMMENT '字段定义Schema(JSON)',
    version VARCHAR(32) DEFAULT '1.0',
    status TINYINT DEFAULT 1,
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_model_code (model_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='主数据模型表';

-- 主数据表
CREATE TABLE master_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    model_id BIGINT NOT NULL COMMENT '模型ID',
    data_code VARCHAR(128) NOT NULL COMMENT '主数据编码',
    data_name VARCHAR(256) NOT NULL COMMENT '主数据名称',
    data_content TEXT COMMENT '主数据内容(JSON)',
    source_system VARCHAR(128) COMMENT '来源系统',
    source_id VARCHAR(128) COMMENT '来源系统ID',
    merge_status VARCHAR(16) DEFAULT 'SINGLE' COMMENT '合并状态: SINGLE-单一, MERGED-已合并, DUPLICATE-重复',
    merge_group_id BIGINT COMMENT '合并组ID',
    quality_score DECIMAL(5,2) COMMENT '质量评分',
    status TINYINT DEFAULT 1,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_model_code (model_id, data_code),
    KEY idx_model_id (model_id),
    KEY idx_merge_group (merge_group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='主数据表';

-- ============================================
-- 6. 数据质量管理模块
-- ============================================

-- 质量规则表
CREATE TABLE data_quality_rule (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    rule_code VARCHAR(128) NOT NULL COMMENT '规则编码',
    rule_name VARCHAR(256) NOT NULL COMMENT '规则名称',
    rule_type VARCHAR(32) NOT NULL COMMENT '规则类型: COMPLETENESS-完整性, ACCURACY-准确性, CONSISTENCY-一致性, TIMELINESS-及时性, UNIQUENESS-唯一性',
    rule_category VARCHAR(64) COMMENT '规则分类',
    description TEXT COMMENT '描述',
    check_expression TEXT NOT NULL COMMENT '检查表达式/SQL',
    threshold_type VARCHAR(16) DEFAULT 'PERCENTAGE' COMMENT '阈值类型: PERCENTAGE-百分比, COUNT-数量',
    threshold_value DECIMAL(10,4) COMMENT '阈值',
    severity VARCHAR(16) DEFAULT 'WARNING' COMMENT '严重级别: INFO, WARNING, ERROR, CRITICAL',
    auto_fix TINYINT DEFAULT 0 COMMENT '是否自动修复',
    fix_expression TEXT COMMENT '修复表达式',
    status TINYINT DEFAULT 1,
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_rule_code (rule_code),
    KEY idx_rule_type (rule_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='质量规则表';

-- 质量检查任务表
CREATE TABLE data_quality_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(256) NOT NULL COMMENT '任务名称',
    task_type VARCHAR(32) NOT NULL COMMENT '任务类型: SCHEDULED-定时, MANUAL-手动, REALTIME-实时',
    source_id BIGINT COMMENT '数据源ID',
    meta_id BIGINT COMMENT '元数据ID',
    rule_ids TEXT COMMENT '关联规则ID列表(JSON)',
    cron_expression VARCHAR(64) COMMENT 'Cron表达式',
    last_run_time DATETIME COMMENT '最后执行时间',
    last_run_status VARCHAR(16) COMMENT '最后执行状态',
    status TINYINT DEFAULT 1,
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_source_id (source_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='质量检查任务表';

-- 质量检查结果表
CREATE TABLE data_quality_result (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL COMMENT '任务ID',
    rule_id BIGINT NOT NULL COMMENT '规则ID',
    source_id BIGINT COMMENT '数据源ID',
    meta_id BIGINT COMMENT '元数据ID',
    check_time DATETIME NOT NULL COMMENT '检查时间',
    total_count BIGINT COMMENT '总记录数',
    error_count BIGINT COMMENT '错误记录数',
    error_rate DECIMAL(10,4) COMMENT '错误率',
    status VARCHAR(16) COMMENT '结果状态: PASS-通过, FAIL-失败',
    error_samples TEXT COMMENT '错误样例(JSON)',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_task_id (task_id),
    KEY idx_rule_id (rule_id),
    KEY idx_check_time (check_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='质量检查结果表';

-- ============================================
-- 7. 数据资产管理模块
-- ============================================

-- 数据资产表
CREATE TABLE data_asset (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asset_code VARCHAR(128) NOT NULL COMMENT '资产编码',
    asset_name VARCHAR(256) NOT NULL COMMENT '资产名称',
    asset_type VARCHAR(32) NOT NULL COMMENT '资产类型: DATASET-数据集, API-接口, REPORT-报告, MODEL-模型',
    asset_status VARCHAR(16) DEFAULT 'DRAFT' COMMENT '资产状态: DRAFT-草稿, PUBLISHED-已发布, OFFLINE-已下线',
    source_id BIGINT COMMENT '数据源ID',
    meta_id BIGINT COMMENT '元数据ID',
    description TEXT COMMENT '描述',
    business_desc TEXT COMMENT '业务说明',
    data_format VARCHAR(32) COMMENT '数据格式',
    data_size BIGINT COMMENT '数据大小(字节)',
    record_count BIGINT COMMENT '记录数',
    field_count INT COMMENT '字段数',
    update_frequency VARCHAR(32) COMMENT '更新频率',
    quality_score DECIMAL(5,2) COMMENT '质量评分',
    owner_id BIGINT COMMENT '负责人ID',
    org_id BIGINT COMMENT '所属机构ID',
    tags TEXT COMMENT '标签(JSON)',
    price DECIMAL(10,2) COMMENT '定价',
    price_unit VARCHAR(16) COMMENT '计价单位',
    publish_time DATETIME COMMENT '发布时间',
    view_count INT DEFAULT 0 COMMENT '浏览次数',
    apply_count INT DEFAULT 0 COMMENT '申请次数',
    download_count INT DEFAULT 0 COMMENT '下载次数',
    status TINYINT DEFAULT 1,
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_asset_code (asset_code),
    KEY idx_asset_type (asset_type),
    KEY idx_org_id (org_id),
    KEY idx_owner_id (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据资产表';

-- 数据资产目录表
CREATE TABLE data_asset_catalog (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    parent_id BIGINT DEFAULT 0 COMMENT '父目录ID',
    catalog_code VARCHAR(128) NOT NULL COMMENT '目录编码',
    catalog_name VARCHAR(256) NOT NULL COMMENT '目录名称',
    catalog_type VARCHAR(32) NOT NULL COMMENT '目录类型: THEME-主题域, BUSINESS-业务线, DOMAIN-数据域',
    description TEXT COMMENT '描述',
    level INT DEFAULT 1 COMMENT '层级',
    status TINYINT DEFAULT 1,
    sort_order INT DEFAULT 0,
    created_by BIGINT,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT DEFAULT 0,
    UNIQUE KEY uk_catalog_code (catalog_code),
    KEY idx_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据资产目录表';

-- 资产目录关联表
CREATE TABLE data_asset_catalog_rel (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    asset_id BIGINT NOT NULL COMMENT '资产ID',
    catalog_id BIGINT NOT NULL COMMENT '目录ID',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_asset_catalog (asset_id, catalog_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资产目录关联表';

-- ============================================
-- 8. 数据交易模块
-- ============================================

-- 数据产品表
CREATE TABLE data_product (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_code VARCHAR(128) NOT NULL COMMENT '产品编码',
    product_name VARCHAR(256) NOT NULL COMMENT '产品名称',
    product_type VARCHAR(32) NOT NULL COMMENT '产品类型: DATASET, API, REPORT, MODEL, SERVICE',
    asset_id BIGINT COMMENT '关联资产ID',
    description TEXT COMMENT '描述',
    data_format VARCHAR(32) COMMENT '数据格式',
    price DECIMAL(10,2) COMMENT '价格',
    price_unit VARCHAR(16) COMMENT '计价单位: PER_USE-按次, PER_MONTH-包月, PER_YEAR-包年, PER_VOLUME-按量',
    delivery_mode VARCHAR(32) COMMENT '交付方式: API, FILE, PRIVACY_COMPUTE',
    status VARCHAR(16) DEFAULT 'DRAFT' COMMENT '状态',
    publish_time DATETIME COMMENT '发布时间',
    owner_id BIGINT COMMENT '发布人',
    org_id BIGINT COMMENT '所属机构',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_product_code (product_code),
    KEY idx_asset_id (asset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据产品表';

-- 数据交易订单表
CREATE TABLE data_trade_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(64) NOT NULL COMMENT '订单编号',
    product_id BIGINT NOT NULL COMMENT '产品ID',
    buyer_id BIGINT NOT NULL COMMENT '买方ID',
    buyer_org_id BIGINT COMMENT '买方机构ID',
    seller_id BIGINT NOT NULL COMMENT '卖方ID',
    seller_org_id BIGINT COMMENT '卖方机构ID',
    price DECIMAL(10,2) COMMENT '成交价格',
    quantity INT DEFAULT 1 COMMENT '数量',
    total_amount DECIMAL(12,2) COMMENT '总金额',
    usage_purpose TEXT COMMENT '使用目的',
    usage_scope TEXT COMMENT '使用范围',
    usage_period INT COMMENT '使用期限(天)',
    contract_no VARCHAR(128) COMMENT '合同编号',
    status VARCHAR(16) DEFAULT 'PENDING' COMMENT '状态: PENDING-待确认, CONFIRMED-已确认, PAID-已支付, DELIVERED-已交付, COMPLETED-已完成, CANCELLED-已取消',
    pay_time DATETIME COMMENT '支付时间',
    deliver_time DATETIME COMMENT '交付时间',
    complete_time DATETIME COMMENT '完成时间',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_order_no (order_no),
    KEY idx_buyer (buyer_id),
    KEY idx_seller (seller_id),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据交易订单表';

-- ============================================
-- 9. AI应用模块
-- ============================================

-- 知识图谱实体表
CREATE TABLE kg_entity (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    entity_id VARCHAR(64) NOT NULL COMMENT '实体唯一ID',
    entity_name VARCHAR(256) NOT NULL COMMENT '实体名称',
    entity_type VARCHAR(32) NOT NULL COMMENT '实体类型: DISEASE-疾病, SYNDROME-证型, SYMPTOM-症状, FORMULA-方剂, HERB-中药, ACUPOINT-穴位, MERIDIAN-经络, DOCTOR-名医',
    aliases TEXT COMMENT '别名列表(JSON)',
    properties TEXT COMMENT '属性(JSON)',
    description TEXT COMMENT '描述',
    source VARCHAR(128) COMMENT '来源',
    source_id VARCHAR(64) COMMENT '来源ID',
    confidence DECIMAL(3,2) DEFAULT 1.00 COMMENT '置信度',
    status TINYINT DEFAULT 1,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_entity_id (entity_id),
    KEY idx_entity_type (entity_type),
    KEY idx_entity_name (entity_name),
    FULLTEXT KEY ft_entity_name (entity_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识图谱实体表';

-- 知识图谱关系表
CREATE TABLE kg_relation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    relation_id VARCHAR(64) NOT NULL COMMENT '关系唯一ID',
    source_entity_id VARCHAR(64) NOT NULL COMMENT '源实体ID',
    target_entity_id VARCHAR(64) NOT NULL COMMENT '目标实体ID',
    relation_type VARCHAR(64) NOT NULL COMMENT '关系类型',
    relation_name VARCHAR(128) COMMENT '关系名称',
    properties TEXT COMMENT '关系属性(JSON)',
    confidence DECIMAL(3,2) DEFAULT 1.00 COMMENT '置信度',
    source VARCHAR(128) COMMENT '来源',
    status TINYINT DEFAULT 1,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_relation (source_entity_id, target_entity_id, relation_type),
    KEY idx_source (source_entity_id),
    KEY idx_target (target_entity_id),
    KEY idx_relation_type (relation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识图谱关系表';

-- AI对话记录表
CREATE TABLE ai_conversation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    conversation_type VARCHAR(32) COMMENT '对话类型: DIAGNOSIS-辅助诊断, CONSTITUTION-体质辨识, KNOWLEDGE-知识问答, PRESCRIPTION-处方辅助',
    user_message TEXT NOT NULL COMMENT '用户消息',
    ai_response TEXT COMMENT 'AI回复',
    context TEXT COMMENT '上下文信息(JSON)',
    model_name VARCHAR(64) COMMENT '使用的模型',
    tokens_used INT COMMENT '使用token数',
    response_time INT COMMENT '响应时间(ms)',
    rating TINYINT COMMENT '用户评分',
    feedback TEXT COMMENT '用户反馈',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_session (session_id),
    KEY idx_user (user_id),
    KEY idx_type (conversation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话记录表';

-- ============================================
-- 10. 审计日志模块
-- ============================================

-- 操作审计日志表
CREATE TABLE audit_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT COMMENT '用户ID',
    username VARCHAR(64) COMMENT '用户名',
    org_id BIGINT COMMENT '机构ID',
    operation_type VARCHAR(32) NOT NULL COMMENT '操作类型: LOGIN, LOGOUT, CREATE, UPDATE, DELETE, QUERY, EXPORT, DOWNLOAD',
    operation_module VARCHAR(64) COMMENT '操作模块',
    operation_desc TEXT COMMENT '操作描述',
    request_method VARCHAR(16) COMMENT '请求方法',
    request_url VARCHAR(512) COMMENT '请求URL',
    request_params TEXT COMMENT '请求参数',
    response_data TEXT COMMENT '响应数据',
    ip_address VARCHAR(64) COMMENT 'IP地址',
    user_agent VARCHAR(512) COMMENT '用户代理',
    execution_time INT COMMENT '执行时间(ms)',
    status TINYINT DEFAULT 1 COMMENT '状态: 0-失败, 1-成功',
    error_msg TEXT COMMENT '错误信息',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user (user_id),
    KEY idx_operation (operation_type),
    KEY idx_time (created_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作审计日志表';

-- 数据访问日志表
CREATE TABLE data_access_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    asset_id BIGINT COMMENT '资产ID',
    access_type VARCHAR(32) NOT NULL COMMENT '访问类型: VIEW-浏览, APPLY-申请, DOWNLOAD-下载, API_CALL-接口调用',
    access_purpose TEXT COMMENT '访问目的',
    data_scope TEXT COMMENT '数据范围',
    row_count BIGINT COMMENT '访问行数',
    ip_address VARCHAR(64) COMMENT 'IP地址',
    status TINYINT DEFAULT 1,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user (user_id),
    KEY idx_asset (asset_id),
    KEY idx_time (created_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据访问日志表';

-- ============================================
-- 初始化数据
-- ============================================

-- 初始化系统管理员
INSERT INTO sys_user (id, username, password, real_name, phone, email, status) VALUES
(1, 'admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5EO', '系统管理员', '13800138000', 'admin@tcm-data.com', 1);

-- 初始化角色
INSERT INTO sys_role (id, role_code, role_name, role_type, description) VALUES
(1, 'SUPER_ADMIN', '超级管理员', 'SYSTEM', '系统最高权限'),
(2, 'ORG_ADMIN', '机构管理员', 'SYSTEM', '机构级别管理员'),
(3, 'DATA_ADMIN', '数据管理员', 'SYSTEM', '数据治理管理员'),
(4, 'DATA_ANALYST', '数据分析师', 'SYSTEM', '数据分析人员'),
(5, 'DOCTOR', '医师', 'SYSTEM', '中医医师'),
(6, 'RESEARCHER', '科研人员', 'SYSTEM', '科研人员');

-- 初始化用户角色关联
INSERT INTO sys_user_role (user_id, role_id) VALUES (1, 1);

-- 初始化数据分级
INSERT INTO data_classification_level (level_code, level_name, level_desc, color, access_control, storage_policy, circulation_policy) VALUES
('L1', '一般数据', '公开或内部数据，泄露后对国家安全、公共利益、个人权益影响轻微', '#52c41a', 
 '{"access":"normal","approval":false}', '{"encryption":false,"backup":"standard"}', '{"share":"open","deidentification":"none"}'),
('L2', '敏感数据', '个人信息与隐私数据，泄露后可能对个人权益造成损害', '#faad14', 
 '{"access":"controlled","approval":true,"audit":true}', '{"encryption":true,"backup":"enhanced"}', '{"share":"restricted","deidentification":"k-anonymity"}'),
('L3', '重要数据', '重要业务数据，泄露后可能对机构运营、行业竞争造成重大影响', '#f5222d', 
 '{"access":"strict","approval":true,"mfa":true,"audit":true}', '{"encryption":"sm4","backup":"disaster_recovery"}', '{"share":"prohibited","deidentification":"differential_privacy"}'),
('L4', '核心数据', '国家核心中医药数据，泄露后可能对国家安全造成严重影响', '#722ed1', 
 '{"access":"top_secret","approval":true,"mfa":true,"audit":true,"watermark":true}', '{"encryption":"sm4","backup":"cross_region","hsm":true}', '{"share":"prohibited","deidentification":"prohibited","tee":true}');

-- 初始化数据分类（业务领域）
INSERT INTO data_classification (class_code, class_name, class_type, description, level) VALUES
('CLINICAL', '临床医疗数据', 'BUSINESS', '中医临床诊疗相关数据', 1),
('HERB', '药材生产数据', 'BUSINESS', '中药材种植、加工、流通数据', 1),
('RESEARCH', '科研教育数据', 'BUSINESS', '中医药科研、教育相关数据', 1),
('ADMIN', '行政管理数据', 'BUSINESS', '中医药行政管理数据', 1),
('INDUSTRY', '产业经济数据', 'BUSINESS', '中医药产业经济统计数据', 1);

-- 初始化数据标准分类
INSERT INTO data_standard_category (category_code, category_name, category_type, description) VALUES
('TCD', '中医病证分类与代码', 'CODING', 'Traditional Chinese Medicine Disease and Syndrome Classification and Codes'),
('ICD11_TM', 'ICD-11传统医学章节', 'CODING', 'ICD-11 Traditional Medicine Conditions'),
('HERB_CODE', '中药编码规则', 'CODING', '中药编码规则及编码'),
('CLINICAL_TERM', '中医临床诊疗术语', 'TERMINOLOGY', '中医临床诊疗术语标准'),
('TCM_NOUN', '中医药学名词', 'TERMINOLOGY', '中医药学名词标准');

-- 初始化主数据模型
INSERT INTO master_data_model (model_code, model_name, model_type, description, fields_schema) VALUES
('PATIENT', '患者主数据', 'PATIENT', '患者基本信息主数据', '{"fields":[{"name":"patient_id","type":"string","required":true},{"name":"name","type":"string","required":true},{"name":"gender","type":"enum","values":["M","F","U"]},{"name":"birth_date","type":"date"},{"name":"phone","type":"string"},{"name":"address","type":"string"}]}'),
('DOCTOR', '医师主数据', 'DOCTOR', '中医医师主数据', '{"fields":[{"name":"doctor_id","type":"string","required":true},{"name":"name","type":"string","required":true},{"name":"title","type":"string"},{"name":"specialty","type":"string"},{"name":"org_id","type":"string"},{"name":"license_no","type":"string"}]}'),
('HERB', '药材主数据', 'HERB', '中药材主数据', '{"fields":[{"name":"herb_id","type":"string","required":true},{"name":"name","type":"string","required":true},{"name":"latin_name","type":"string"},{"name":"pinyin","type":"string"},{"name":"category","type":"string"},{"name":"origin","type":"string"}]}'),
('FORMULA', '方剂主数据', 'FORMULA', '中医方剂主数据', '{"fields":[{"name":"formula_id","type":"string","required":true},{"name":"name","type":"string","required":true},{"name":"source","type":"string"},{"name":"composition","type":"array"},{"name":"indications","type":"string"},{"name":"effects","type":"string"}]}'),
('DISEASE', '病证主数据', 'DISEASE', '中医病证主数据', '{"fields":[{"name":"disease_id","type":"string","required":true},{"name":"name","type":"string","required":true},{"name":"tcd_code","type":"string"},{"name":"icd_code","type":"string"},{"name":"category","type":"string"},{"name":"symptoms","type":"array"}]}');

-- 初始化质量规则
INSERT INTO data_quality_rule (rule_code, rule_name, rule_type, rule_category, description, check_expression, threshold_type, threshold_value, severity) VALUES
('RULE_001', '非空检查', 'COMPLETENESS', '基础检查', '检查字段值是否为空', 'SELECT COUNT(*) FROM {table} WHERE {column} IS NULL OR {column} = ""', 'PERCENTAGE', 5.00, 'ERROR'),
('RULE_002', '唯一性检查', 'UNIQUENESS', '基础检查', '检查字段值是否唯一', 'SELECT {column}, COUNT(*) as cnt FROM {table} GROUP BY {column} HAVING cnt > 1', 'COUNT', 0, 'ERROR'),
('RULE_003', '手机号格式检查', 'ACCURACY', '格式检查', '检查手机号格式是否正确', 'SELECT COUNT(*) FROM {table} WHERE {column} NOT REGEXP "^1[3-9][0-9]{9}$"', 'PERCENTAGE', 1.00, 'WARNING'),
('RULE_004', '身份证格式检查', 'ACCURACY', '格式检查', '检查身份证号格式是否正确', 'SELECT COUNT(*) FROM {table} WHERE {column} NOT REGEXP "^[1-9][0-9]{16}[0-9Xx]$"', 'PERCENTAGE', 1.00, 'WARNING'),
('RULE_005', '日期范围检查', 'ACCURACY', '范围检查', '检查日期是否在合理范围内', 'SELECT COUNT(*) FROM {table} WHERE {column} > CURDATE() OR {column} < "1900-01-01"', 'PERCENTAGE', 0.50, 'ERROR'),
('RULE_006', '枚举值检查', 'ACCURACY', '值域检查', '检查字段值是否在允许范围内', 'SELECT COUNT(*) FROM {table} WHERE {column} NOT IN {allowed_values}', 'PERCENTAGE', 1.00, 'ERROR'),
('RULE_007', '数据时效性检查', 'TIMELINESS', '时效检查', '检查数据更新是否及时', 'SELECT DATEDIFF(CURDATE(), MAX(update_time)) as days FROM {table}', 'COUNT', 30, 'WARNING');
