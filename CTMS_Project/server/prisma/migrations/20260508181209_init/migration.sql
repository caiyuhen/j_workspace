-- Initial database schema for CTMS+EDC v4.0
-- Including CDISC / CDASH alignment supplement for EDC forms and controls

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "username" VARCHAR(100) NOT NULL,
    "email" VARCHAR(200) NOT NULL,
    "password_hash" VARCHAR(255) NOT NULL,
    "display_name" VARCHAR(200) NOT NULL,
    "phone" VARCHAR(50),
    "title" VARCHAR(200),
    "department" VARCHAR(200),
    "organization" VARCHAR(200),
    "avatar_url" VARCHAR(500),
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "last_login_at" TIMESTAMPTZ(6),
    "password_changed_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "roles" (
    "id" TEXT NOT NULL,
    "role_code" VARCHAR(50) NOT NULL,
    "role_name" VARCHAR(100) NOT NULL,
    "description" VARCHAR(500),
    "is_system_role" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "roles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_roles" (
    "id" TEXT NOT NULL,
    "user_id" VARCHAR(36) NOT NULL,
    "role_id" VARCHAR(36) NOT NULL,
    "project_id" VARCHAR(36),
    "site_id" VARCHAR(36),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "user_roles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "permissions" (
    "id" TEXT NOT NULL,
    "permission_code" VARCHAR(100) NOT NULL,
    "permission_name" VARCHAR(200) NOT NULL,
    "permission_type" VARCHAR(20) NOT NULL,
    "resource_type" VARCHAR(50),
    "action_type" VARCHAR(50),
    "description" VARCHAR(500),
    "is_system_permission" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "permissions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "role_permissions" (
    "id" TEXT NOT NULL,
    "role_id" VARCHAR(36) NOT NULL,
    "permission_id" VARCHAR(36) NOT NULL,
    "resource_scope" VARCHAR(20) NOT NULL DEFAULT 'all',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "role_permissions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "organizations" (
    "id" TEXT NOT NULL,
    "org_code" VARCHAR(100) NOT NULL,
    "org_name" VARCHAR(200) NOT NULL,
    "org_type" VARCHAR(50) NOT NULL,
    "address" VARCHAR(500),
    "contact_person" VARCHAR(200),
    "contact_phone" VARCHAR(50),
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,
    "city" VARCHAR(100),
    "contact_email" VARCHAR(200),
    "country" VARCHAR(50) DEFAULT 'China',
    "description" TEXT,
    "parent_id" VARCHAR(36),
    "province" VARCHAR(100),
    "short_name" VARCHAR(100),
    "sort_order" INTEGER NOT NULL DEFAULT 0,
    "gcp_contact_name" VARCHAR(200),
    "gcp_contact_phone" VARCHAR(50),
    "research_contact_name" VARCHAR(200),
    "research_contact_phone" VARCHAR(50),
    "investigator_name" VARCHAR(200),

    CONSTRAINT "organizations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "projects" (
    "id" TEXT NOT NULL,
    "project_code" VARCHAR(100) NOT NULL,
    "project_name" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "study_type" VARCHAR(50),
    "therapeutic_area" VARCHAR(200),
    "indication" VARCHAR(300),
    "blind_type" VARCHAR(50),
    "sample_size" INTEGER,
    "start_date" DATE,
    "end_date" DATE,
    "total_budget" DOUBLE PRECISION,
    "currency" VARCHAR(10) DEFAULT 'CNY',
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "status_reason" VARCHAR(500),
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,
    "phase" VARCHAR(20),

    CONSTRAINT "projects_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "milestones" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "milestone_name" VARCHAR(200) NOT NULL,
    "milestone_type" VARCHAR(50) NOT NULL,
    "planned_date" DATE NOT NULL,
    "actual_date" DATE,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "description" TEXT,
    "sort_order" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "milestones_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "sites" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36),
    "site_code" VARCHAR(100) NOT NULL,
    "site_name" VARCHAR(200) NOT NULL,
    "pi_user_id" VARCHAR(36),
    "address" VARCHAR(500),
    "contact_phone" VARCHAR(50),
    "ethics_status" VARCHAR(50),
    "ethics_approve_date" DATE,
    "contract_status" VARCHAR(50),
    "planned_sample_size" INTEGER,
    "gcp_contact_name" VARCHAR(200),
    "gcp_contact_phone" VARCHAR(50),
    "research_contact_name" VARCHAR(200),
    "research_contact_phone" VARCHAR(50),
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "sites_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "site_staff" (
    "id" TEXT NOT NULL,
    "site_id" VARCHAR(36) NOT NULL,
    "user_id" VARCHAR(36) NOT NULL,
    "role_at_site" VARCHAR(50) NOT NULL,
    "joined_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "left_at" TIMESTAMPTZ(6),
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',

    CONSTRAINT "site_staff_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "monitoring_plans" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "plan_name" VARCHAR(200) NOT NULL,
    "frequency" VARCHAR(100),
    "description" TEXT,
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "monitoring_plans_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "monitoring_visits" (
    "id" TEXT NOT NULL,
    "plan_id" VARCHAR(36),
    "project_id" VARCHAR(36) NOT NULL,
    "site_id" VARCHAR(36),
    "cra_user_id" VARCHAR(36) NOT NULL,
    "visit_type" VARCHAR(50) NOT NULL,
    "planned_date" DATE NOT NULL,
    "actual_date" DATE,
    "status" VARCHAR(20) NOT NULL DEFAULT 'planned',
    "sdv_percentage" DOUBLE PRECISION,
    "report_id" VARCHAR(36),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "monitoring_visits_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "timesheets" (
    "id" TEXT NOT NULL,
    "user_id" VARCHAR(36) NOT NULL,
    "project_id" VARCHAR(36),
    "week_start_date" DATE NOT NULL,
    "total_hours" DOUBLE PRECISION NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "submitted_at" TIMESTAMPTZ(6),
    "approved_by" VARCHAR(36),
    "approved_at" TIMESTAMPTZ(6),
    "rejection_reason" VARCHAR(500),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "timesheets_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "timesheet_entries" (
    "id" TEXT NOT NULL,
    "timesheet_id" VARCHAR(36) NOT NULL,
    "work_date" DATE NOT NULL,
    "hours" DOUBLE PRECISION NOT NULL,
    "work_type" VARCHAR(20) NOT NULL,
    "project_id" VARCHAR(36),
    "site_id" VARCHAR(36),
    "description" VARCHAR(500),
    "is_billable" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "timesheet_entries_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "financial_incomes" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36),
    "income_code" VARCHAR(100) NOT NULL,
    "income_type" VARCHAR(20) NOT NULL,
    "description" VARCHAR(300),
    "amount" DOUBLE PRECISION NOT NULL,
    "currency" VARCHAR(10) NOT NULL DEFAULT 'CNY',
    "expected_date" DATE,
    "received_date" DATE,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "invoice_id" VARCHAR(36),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "financial_incomes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "financial_expenses" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36),
    "expense_code" VARCHAR(100) NOT NULL,
    "expense_type" VARCHAR(20) NOT NULL,
    "description" VARCHAR(300),
    "amount" DOUBLE PRECISION NOT NULL,
    "currency" VARCHAR(10) NOT NULL DEFAULT 'CNY',
    "expense_date" DATE NOT NULL,
    "submitted_by" VARCHAR(36) NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "reimbursement_status" VARCHAR(20),
    "invoice_url" VARCHAR(500),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "financial_expenses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "subjects" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "site_id" VARCHAR(36),
    "subject_code" VARCHAR(100) NOT NULL,
    "screening_number" VARCHAR(100),
    "randomization_number" VARCHAR(50),
    "enrollment_status" VARCHAR(20) NOT NULL DEFAULT 'screening',
    "screening_failed_reason" VARCHAR(500),
    "enrolled_at" TIMESTAMPTZ(6),
    "discontinued_at" TIMESTAMPTZ(6),
    "discontinuation_reason" VARCHAR(500),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "subjects_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "visits" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "subject_id" VARCHAR(36),
    "site_id" VARCHAR(36),
    "visit_code" VARCHAR(100) NOT NULL,
    "visit_name" VARCHAR(200) NOT NULL,
    "planned_date" DATE,
    "actual_date" DATE,
    "status" VARCHAR(20) NOT NULL DEFAULT 'planned',
    "is_sdv_completed" BOOLEAN NOT NULL DEFAULT false,
    "sdv_completed_by" VARCHAR(36),
    "sdv_completed_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "visits_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "edc_templates" (
    "id" TEXT NOT NULL,
    "template_code" VARCHAR(100) NOT NULL,
    "template_name" VARCHAR(200) NOT NULL,
    "template_type" VARCHAR(20) NOT NULL,
    "therapeutic_area" VARCHAR(100),
    "indication" VARCHAR(200),
    "description" TEXT,
    "version" VARCHAR(20) NOT NULL DEFAULT '1.0',
    "is_system_template" BOOLEAN NOT NULL DEFAULT false,
    "is_shared" BOOLEAN NOT NULL DEFAULT false,
    "owner_user_id" VARCHAR(36),
    "project_id" VARCHAR(36),
    "template_data" JSONB NOT NULL DEFAULT '{}',
    "usage_count" INTEGER NOT NULL DEFAULT 0,
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "published_at" TIMESTAMPTZ(6),
    "published_by" VARCHAR(36),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "edc_templates_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crf_data" (
    "id" TEXT NOT NULL,
    "subject_id" VARCHAR(36) NOT NULL,
    "visit_id" VARCHAR(36),
    "form_id" VARCHAR(100) NOT NULL,
    "form_code" VARCHAR(100) NOT NULL,
    "field_id" VARCHAR(100) NOT NULL,
    "field_code" VARCHAR(100) NOT NULL,
    "field_value" TEXT,
    "raw_value" JSONB,
    "standardized_value" JSONB,
    "form_data" JSONB,
    "cdisc_domain" VARCHAR(10),
    "cdash_dataset" VARCHAR(50),
    "cdash_variable" VARCHAR(40),
    "sdtm_variable" VARCHAR(40),
    "code_list_oid" VARCHAR(100),
    "collection_version" VARCHAR(20),
    "entered_by" VARCHAR(36) NOT NULL,
    "entered_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_by" VARCHAR(36),
    "updated_at" TIMESTAMPTZ(6),
    "is_deleted" BOOLEAN NOT NULL DEFAULT false,
    "deleted_by" VARCHAR(36),
    "deleted_at" TIMESTAMPTZ(6),
    "audit_trail" JSONB,
    "esig_status" VARCHAR(20),
    "esig_signed_by" VARCHAR(36),
    "esig_signed_at" TIMESTAMPTZ(6),

    CONSTRAINT "crf_data_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crf_data_history" (
    "id" TEXT NOT NULL,
    "crf_data_id" VARCHAR(36) NOT NULL,
    "field_id" VARCHAR(100) NOT NULL,
    "old_value" JSONB,
    "new_value" JSONB,
    "change_reason" VARCHAR(500),
    "changed_by" VARCHAR(36) NOT NULL,
    "changed_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "crf_data_history_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "data_queries" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "subject_id" VARCHAR(36),
    "visit_id" VARCHAR(36),
    "form_id" VARCHAR(100),
    "field_id" VARCHAR(100),
    "query_type" VARCHAR(50) NOT NULL,
    "priority" VARCHAR(20) NOT NULL DEFAULT 'normal',
    "title" VARCHAR(300) NOT NULL,
    "description" TEXT NOT NULL,
    "assigned_to" VARCHAR(36),
    "raised_by" VARCHAR(36) NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'open',
    "due_date" DATE,
    "answered_at" TIMESTAMPTZ(6),
    "answer" TEXT,
    "closed_at" TIMESTAMPTZ(6),
    "closed_by" VARCHAR(36),
    "escalation_level" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "data_queries_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "data_query_histories" (
    "id" TEXT NOT NULL,
    "query_id" VARCHAR(36) NOT NULL,
    "action_type" VARCHAR(20) NOT NULL,
    "action_by" VARCHAR(36) NOT NULL,
    "action_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "old_value" JSONB,
    "new_value" JSONB,
    "reason" TEXT,

    CONSTRAINT "data_query_histories_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "edc_randomization_records" (
    "id" TEXT NOT NULL,
    "subject_id" VARCHAR(36) NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "randomization_number" VARCHAR(50) NOT NULL,
    "treatment_arm" VARCHAR(100),
    "randomization_date" TIMESTAMPTZ(6) NOT NULL,
    "method" VARCHAR(50),
    "stratified_factors" JSONB,
    "drug_batch" VARCHAR(50),
    "drug_expiry_date" DATE,
    "randomized_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "edc_randomization_records_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "edc_lock_records" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "lock_type" VARCHAR(20) NOT NULL,
    "target_id" VARCHAR(36) NOT NULL,
    "lock_reason" TEXT,
    "locked_by" VARCHAR(36) NOT NULL,
    "locked_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "unlock_approved_by" VARCHAR(36),
    "unlock_at" TIMESTAMPTZ(6),
    "status" VARCHAR(20) NOT NULL DEFAULT 'locked',
    "esig_records" JSONB,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "edc_lock_records_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "workflow_definitions" (
    "id" TEXT NOT NULL,
    "workflow_code" VARCHAR(100) NOT NULL,
    "workflow_name" VARCHAR(200) NOT NULL,
    "workflow_type" VARCHAR(50) NOT NULL,
    "is_template" BOOLEAN NOT NULL DEFAULT false,
    "stages" JSONB NOT NULL DEFAULT '[]',
    "allow_delegate" BOOLEAN NOT NULL DEFAULT true,
    "notification_enabled" BOOLEAN NOT NULL DEFAULT true,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "workflow_definitions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "workflow_instances" (
    "id" TEXT NOT NULL,
    "definition_id" VARCHAR(36) NOT NULL,
    "workflow_type" VARCHAR(50) NOT NULL,
    "initiator_id" VARCHAR(36) NOT NULL,
    "project_id" VARCHAR(36),
    "business_data" JSONB,
    "current_stage_index" INTEGER NOT NULL DEFAULT 0,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "completed_at" TIMESTAMPTZ(6),
    "result" VARCHAR(20),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "workflow_instances_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "workflow_tasks" (
    "id" TEXT NOT NULL,
    "instance_id" VARCHAR(36) NOT NULL,
    "stage_id" VARCHAR(100) NOT NULL,
    "stage_name" VARCHAR(200) NOT NULL,
    "assigned_to" VARCHAR(36) NOT NULL,
    "approver_role" VARCHAR(50),
    "esig_required" BOOLEAN NOT NULL DEFAULT false,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "action" VARCHAR(20),
    "comment" TEXT,
    "esig_data" JSONB,
    "due_at" TIMESTAMPTZ(6),
    "completed_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "countersign_approvers" JSONB DEFAULT '[]',
    "countersign_completed" JSONB DEFAULT '[]',
    "is_countersign" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "workflow_tasks_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "unified_audit_logs" (
    "id" TEXT NOT NULL,
    "system_code" VARCHAR(10) NOT NULL,
    "project_id" VARCHAR(36),
    "user_id" VARCHAR(36) NOT NULL,
    "session_id" VARCHAR(50),
    "ip_address" VARCHAR(50),
    "event_type" VARCHAR(50) NOT NULL,
    "event_category" VARCHAR(30),
    "table_name" VARCHAR(100),
    "record_id" VARCHAR(36),
    "action" VARCHAR(100) NOT NULL,
    "old_values" JSONB,
    "new_values" JSONB,
    "changed_fields" JSONB,
    "regulatory_ref" VARCHAR(100),
    "previous_hash" VARCHAR(64),
    "current_hash" VARCHAR(64),
    "signature_id" VARCHAR(36),
    "event_timestamp" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "unified_audit_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "notifications" (
    "id" TEXT NOT NULL,
    "recipient_id" VARCHAR(36) NOT NULL,
    "channel" VARCHAR(20) NOT NULL,
    "title" VARCHAR(500) NOT NULL,
    "content" TEXT NOT NULL,
    "business_type" VARCHAR(50),
    "business_id" VARCHAR(36),
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "sent_at" TIMESTAMPTZ(6),
    "delivered_at" TIMESTAMPTZ(6),
    "read_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "notifications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crf_forms" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "form_code" VARCHAR(100) NOT NULL,
    "form_name" VARCHAR(200) NOT NULL,
    "form_type" VARCHAR(50) NOT NULL,
    "standard_name" VARCHAR(50) DEFAULT 'CDASH',
    "standard_version" VARCHAR(20) DEFAULT '2.1',
    "cdisc_domain" VARCHAR(10),
    "cdash_model" VARCHAR(50),
    "sdtm_dataset_name" VARCHAR(10),
    "implementation_guide" VARCHAR(100),
    "description" TEXT,
    "form_metadata" JSONB DEFAULT '{}',
    "version" VARCHAR(20) NOT NULL DEFAULT '1.0',
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "published_at" TIMESTAMPTZ(6),
    "published_by" VARCHAR(36),
    "is_repeating" BOOLEAN NOT NULL DEFAULT false,
    "max_repeats" INTEGER,
    "visit_window" VARCHAR(100),
    "sort_order" INTEGER NOT NULL DEFAULT 0,
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "crf_forms_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crf_form_fields" (
    "id" TEXT NOT NULL,
    "form_id" VARCHAR(36) NOT NULL,
    "field_code" VARCHAR(100) NOT NULL,
    "field_name" VARCHAR(200) NOT NULL,
    "field_type" VARCHAR(50) NOT NULL,
    "control_type" VARCHAR(50) NOT NULL DEFAULT 'input',
    "description" VARCHAR(500),
    "placeholder" VARCHAR(200),
    "question_text" VARCHAR(500),
    "default_value" TEXT,
    "required" BOOLEAN NOT NULL DEFAULT false,
    "max_length" INTEGER,
    "min_value" DOUBLE PRECISION,
    "max_value" DOUBLE PRECISION,
    "display_format" VARCHAR(100),
    "origin" VARCHAR(50),
    "validation_regex" VARCHAR(500),
    "options" JSONB DEFAULT '[]',
    "unit" VARCHAR(50),
    "sort_order" INTEGER NOT NULL DEFAULT 0,
    "parent_field_id" VARCHAR(36),
    "dependency_rule" JSONB,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,
    "cdisc_domain" VARCHAR(10),
    "cdash_dataset" VARCHAR(50),
    "cdash_variable" VARCHAR(40),
    "cdash_data_type" VARCHAR(20),
    "code_list_oid" VARCHAR(100),
    "cdash_prompt" VARCHAR(500),
    "sdtm_variable" VARCHAR(40),
    "sdtm_role" VARCHAR(20),
    "implementation_class" VARCHAR(50),
    "standard_metadata" JSONB DEFAULT '{}',

    CONSTRAINT "crf_form_fields_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crf_edit_check_rules" (
    "id" TEXT NOT NULL,
    "form_id" VARCHAR(36) NOT NULL,
    "rule_code" VARCHAR(100) NOT NULL,
    "rule_name" VARCHAR(200) NOT NULL,
    "rule_type" VARCHAR(50) NOT NULL,
    "description" TEXT,
    "expression" TEXT NOT NULL,
    "error_message" VARCHAR(500) NOT NULL,
    "severity" VARCHAR(20) NOT NULL DEFAULT 'warning',
    "target_field_ids" JSONB NOT NULL DEFAULT '[]',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "crf_edit_check_rules_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crf_form_versions" (
    "id" TEXT NOT NULL,
    "form_id" VARCHAR(36) NOT NULL,
    "version" VARCHAR(20) NOT NULL,
    "changeLog" TEXT,
    "form_data" JSONB NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'released',
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "crf_form_versions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crf_form_publications" (
    "id" TEXT NOT NULL,
    "form_id" VARCHAR(36) NOT NULL,
    "version" VARCHAR(20) NOT NULL,
    "scope_type" VARCHAR(20) NOT NULL,
    "target_ids" JSONB NOT NULL DEFAULT '[]',
    "published_by" VARCHAR(36) NOT NULL,
    "published_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "effective_date" TIMESTAMPTZ(6) NOT NULL,
    "notes" TEXT,

    CONSTRAINT "crf_form_publications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "drugs" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "drug_code" VARCHAR(100) NOT NULL,
    "drug_name" VARCHAR(200) NOT NULL,
    "generic_name" VARCHAR(200),
    "dosage_form" VARCHAR(100),
    "strength" VARCHAR(100),
    "manufacturer" VARCHAR(200),
    "storage_condition" VARCHAR(500),
    "temperature_min" DOUBLE PRECISION,
    "temperature_max" DOUBLE PRECISION,
    "shelf_life" INTEGER,
    "shelf_life_unit" VARCHAR(20),
    "is_blinded" BOOLEAN NOT NULL DEFAULT false,
    "description" TEXT,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "drugs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "drug_supply_plans" (
    "id" TEXT NOT NULL,
    "drug_id" VARCHAR(36) NOT NULL,
    "plan_name" VARCHAR(200) NOT NULL,
    "planned_date" DATE NOT NULL,
    "quantity" INTEGER NOT NULL,
    "batch_number" VARCHAR(100),
    "expiry_date" DATE,
    "status" VARCHAR(20) NOT NULL DEFAULT 'planned',
    "notes" TEXT,
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "drug_supply_plans_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "drug_shipments" (
    "id" TEXT NOT NULL,
    "drug_id" VARCHAR(36) NOT NULL,
    "shipment_code" VARCHAR(100) NOT NULL,
    "from_location" VARCHAR(200) NOT NULL,
    "to_site_id" VARCHAR(36),
    "to_location" VARCHAR(200),
    "quantity" INTEGER NOT NULL,
    "batch_number" VARCHAR(100) NOT NULL,
    "expiry_date" DATE NOT NULL,
    "shipped_date" TIMESTAMPTZ(6) NOT NULL,
    "received_date" TIMESTAMPTZ(6),
    "received_by" VARCHAR(36),
    "temperature_ok" BOOLEAN,
    "temperature_log" JSONB,
    "courier" VARCHAR(200),
    "tracking_number" VARCHAR(100),
    "status" VARCHAR(20) NOT NULL DEFAULT 'shipped',
    "notes" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "drug_shipments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "drug_inventories" (
    "id" TEXT NOT NULL,
    "drug_id" VARCHAR(36) NOT NULL,
    "site_id" VARCHAR(36),
    "location" VARCHAR(200) NOT NULL,
    "batch_number" VARCHAR(100) NOT NULL,
    "expiry_date" DATE NOT NULL,
    "quantity_on_hand" INTEGER NOT NULL,
    "quantity_reserved" INTEGER NOT NULL DEFAULT 0,
    "quantity_dispensed" INTEGER NOT NULL DEFAULT 0,
    "last_count_date" TIMESTAMPTZ(6),
    "status" VARCHAR(20) NOT NULL DEFAULT 'normal',
    "notes" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "drug_inventories_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "drug_destructions" (
    "id" TEXT NOT NULL,
    "drug_id" VARCHAR(36) NOT NULL,
    "site_id" VARCHAR(36),
    "batch_number" VARCHAR(100) NOT NULL,
    "quantity" INTEGER NOT NULL,
    "destruction_date" TIMESTAMPTZ(6) NOT NULL,
    "destruction_method" VARCHAR(200) NOT NULL,
    "reason" TEXT NOT NULL,
    "witness_ids" JSONB NOT NULL DEFAULT '[]',
    "performed_by" VARCHAR(36) NOT NULL,
    "certificate_url" VARCHAR(500),
    "status" VARCHAR(20) NOT NULL DEFAULT 'completed',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "drug_destructions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "tmf_documents" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "tmf_section" VARCHAR(50) NOT NULL,
    "document_code" VARCHAR(100) NOT NULL,
    "document_name" VARCHAR(300) NOT NULL,
    "document_type" VARCHAR(50) NOT NULL,
    "description" TEXT,
    "file_url" VARCHAR(500),
    "file_size" INTEGER,
    "mime_type" VARCHAR(100),
    "version" VARCHAR(20) NOT NULL DEFAULT '1.0',
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "is_required" BOOLEAN NOT NULL DEFAULT false,
    "expected_date" DATE,
    "received_date" DATE,
    "expiry_date" DATE,
    "uploaded_by" VARCHAR(36),
    "tags" JSONB DEFAULT '[]',
    "metadata" JSONB,
    "parent_document_id" VARCHAR(36),
    "zonal_type" VARCHAR(20),
    "country" VARCHAR(50),
    "site_id" VARCHAR(36),
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "tmf_documents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "tmf_document_versions" (
    "id" TEXT NOT NULL,
    "document_id" VARCHAR(36) NOT NULL,
    "version" VARCHAR(20) NOT NULL,
    "changeLog" TEXT,
    "file_url" VARCHAR(500) NOT NULL,
    "file_size" INTEGER,
    "mime_type" VARCHAR(100),
    "uploaded_by" VARCHAR(36) NOT NULL,
    "uploaded_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "tmf_document_versions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "sdv_records" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "site_id" VARCHAR(36) NOT NULL,
    "subject_id" VARCHAR(36) NOT NULL,
    "visit_id" VARCHAR(36),
    "form_id" VARCHAR(36),
    "cra_user_id" VARCHAR(36) NOT NULL,
    "monitoring_visit_id" VARCHAR(36),
    "sdv_date" TIMESTAMPTZ(6) NOT NULL,
    "total_items" INTEGER NOT NULL DEFAULT 0,
    "verified_items" INTEGER NOT NULL DEFAULT 0,
    "discrepancy_items" INTEGER NOT NULL DEFAULT 0,
    "percentage" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "notes" TEXT,
    "status" VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    "completed_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "sdv_records_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "sdv_items" (
    "id" TEXT NOT NULL,
    "sdv_record_id" VARCHAR(36) NOT NULL,
    "crf_data_id" VARCHAR(36) NOT NULL,
    "field_code" VARCHAR(100) NOT NULL,
    "crf_value" TEXT,
    "source_value" TEXT,
    "is_verified" BOOLEAN NOT NULL DEFAULT false,
    "is_match" BOOLEAN,
    "discrepancy_type" VARCHAR(50),
    "comment" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "sdv_items_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "adverse_events" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "subject_id" VARCHAR(36) NOT NULL,
    "report_code" VARCHAR(100) NOT NULL,
    "event_type" VARCHAR(20) NOT NULL,
    "term_preferred" VARCHAR(500) NOT NULL,
    "term_code" VARCHAR(50),
    "meddra_code" VARCHAR(50),
    "onset_date" DATE NOT NULL,
    "end_date" DATE,
    "is_ongoing" BOOLEAN NOT NULL DEFAULT true,
    "severity" VARCHAR(20) NOT NULL,
    "seriousness" VARCHAR(20) NOT NULL,
    "seriousness_criteria" JSONB NOT NULL DEFAULT '[]',
    "causality" VARCHAR(50),
    "causality_method" VARCHAR(50),
    "relationship" VARCHAR(50),
    "description" TEXT NOT NULL,
    "action_taken" JSONB NOT NULL DEFAULT '[]',
    "outcome" VARCHAR(100),
    "reporter_id" VARCHAR(36) NOT NULL,
    "site_id" VARCHAR(36),
    "status" VARCHAR(20) NOT NULL DEFAULT 'open',
    "reported_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "adverse_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "sae_reports" (
    "id" TEXT NOT NULL,
    "adverse_event_id" VARCHAR(36) NOT NULL,
    "report_type" VARCHAR(50) NOT NULL,
    "report_version" VARCHAR(20) NOT NULL,
    "regulatory_body" VARCHAR(200),
    "report_date" TIMESTAMPTZ(6) NOT NULL,
    "submission_deadline" TIMESTAMPTZ(6),
    "actual_submission_date" TIMESTAMPTZ(6),
    "report_content" JSONB NOT NULL DEFAULT '{}',
    "review_status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "reviewed_by" VARCHAR(36),
    "reviewed_at" TIMESTAMPTZ(6),
    "review_comments" TEXT,
    "submitted_to" VARCHAR(200),
    "submission_ref" VARCHAR(200),
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "submitted_by" VARCHAR(36),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "sae_reports_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_agent_logs" (
    "id" TEXT NOT NULL,
    "agent_type" VARCHAR(50) NOT NULL,
    "project_id" VARCHAR(36),
    "user_id" VARCHAR(36) NOT NULL,
    "input" JSONB NOT NULL,
    "output" JSONB,
    "context_data" JSONB,
    "model_used" VARCHAR(100),
    "tokens_used" INTEGER DEFAULT 0,
    "duration_ms" INTEGER,
    "status" VARCHAR(20) NOT NULL DEFAULT 'success',
    "error_message" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_agent_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "system_configs" (
    "id" TEXT NOT NULL,
    "config_key" VARCHAR(100) NOT NULL,
    "config_value" TEXT,
    "config_type" VARCHAR(20) NOT NULL DEFAULT 'string',
    "description" VARCHAR(500),
    "is_encrypted" BOOLEAN NOT NULL DEFAULT false,
    "scope" VARCHAR(20) NOT NULL DEFAULT 'global',
    "scope_id" VARCHAR(36),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "system_configs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "vendors" (
    "id" TEXT NOT NULL,
    "vendor_code" VARCHAR(100) NOT NULL,
    "vendor_name" VARCHAR(200) NOT NULL,
    "vendor_type" VARCHAR(50) NOT NULL,
    "contact_person" VARCHAR(200),
    "contact_phone" VARCHAR(50),
    "contact_email" VARCHAR(200),
    "address" VARCHAR(500),
    "qualification" JSONB,
    "rating" DOUBLE PRECISION DEFAULT 0,
    "description" TEXT,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "vendors_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "contracts" (
    "id" TEXT NOT NULL,
    "contract_code" VARCHAR(100) NOT NULL,
    "contract_name" VARCHAR(300) NOT NULL,
    "contract_type" VARCHAR(50) NOT NULL,
    "vendor_id" VARCHAR(36),
    "project_id" VARCHAR(36),
    "amount" DOUBLE PRECISION,
    "currency" VARCHAR(10) NOT NULL DEFAULT 'CNY',
    "start_date" DATE,
    "end_date" DATE,
    "sign_status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "version" VARCHAR(20) NOT NULL DEFAULT '1.0',
    "attachment_url" VARCHAR(500),
    "description" TEXT,
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "contracts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ethics_approvals" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "site_id" VARCHAR(36),
    "ethics_committee" VARCHAR(200) NOT NULL,
    "approval_type" VARCHAR(50) NOT NULL,
    "approval_number" VARCHAR(100),
    "submission_date" DATE,
    "approval_date" DATE,
    "expiry_date" DATE,
    "approval_status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "document_url" VARCHAR(500),
    "notes" TEXT,
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "ethics_approvals_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "data_sync_logs" (
    "id" TEXT NOT NULL,
    "sync_type" VARCHAR(50) NOT NULL,
    "direction" VARCHAR(20) NOT NULL,
    "project_id" VARCHAR(36),
    "source_system" VARCHAR(10) NOT NULL,
    "target_system" VARCHAR(10) NOT NULL,
    "record_id" VARCHAR(36),
    "record_type" VARCHAR(50),
    "payload" JSONB,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "error_message" TEXT,
    "retry_count" INTEGER NOT NULL DEFAULT 0,
    "synced_at" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "data_sync_logs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "query_histories" (
    "id" TEXT NOT NULL,
    "query_id" VARCHAR(36) NOT NULL,
    "action_type" VARCHAR(20) NOT NULL,
    "action_by" VARCHAR(36) NOT NULL,
    "old_value" JSONB,
    "new_value" JSONB,
    "reason" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "query_histories_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "wechat_user_bindings" (
    "id" TEXT NOT NULL,
    "user_id" VARCHAR(36) NOT NULL,
    "channel" VARCHAR(10) NOT NULL,
    "open_id" VARCHAR(100),
    "union_id" VARCHAR(100),
    "wecom_user_id" VARCHAR(100),
    "bind_status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "bind_time" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "unbind_time" TIMESTAMPTZ(6),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "wechat_user_bindings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "consent_records" (
    "id" TEXT NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "site_id" VARCHAR(36) NOT NULL,
    "subject_id" VARCHAR(36) NOT NULL,
    "consent_version" VARCHAR(20) NOT NULL,
    "consent_date" TIMESTAMPTZ(6) NOT NULL,
    "signee_type" VARCHAR(50) NOT NULL,
    "signee_name" VARCHAR(200) NOT NULL,
    "reconsent_reason" TEXT,
    "document_url" VARCHAR(500),
    "signature_id" VARCHAR(36),
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "consent_records_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "abac_policies" (
    "id" TEXT NOT NULL,
    "policy_code" VARCHAR(100) NOT NULL,
    "policy_name" VARCHAR(200) NOT NULL,
    "resources" JSONB NOT NULL,
    "conditions" JSONB NOT NULL,
    "effect" VARCHAR(20) NOT NULL DEFAULT 'permit',
    "deny_otherwise" BOOLEAN NOT NULL DEFAULT false,
    "priority" INTEGER NOT NULL DEFAULT 0,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "description" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "abac_policies_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "signature_records" (
    "id" TEXT NOT NULL,
    "user_id" VARCHAR(36) NOT NULL,
    "project_id" VARCHAR(36),
    "signature_meaning" VARCHAR(200) NOT NULL,
    "signature_reason" VARCHAR(500) NOT NULL,
    "table_name" VARCHAR(100),
    "record_id" VARCHAR(36),
    "previous_hash" VARCHAR(64),
    "current_hash" VARCHAR(64),
    "ip_address" VARCHAR(50),
    "user_agent" VARCHAR(500),
    "signed_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "signature_records_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "data_masking_rules" (
    "id" TEXT NOT NULL,
    "rule_name" VARCHAR(200) NOT NULL,
    "table_name" VARCHAR(100) NOT NULL,
    "field_name" VARCHAR(100) NOT NULL,
    "mask_type" VARCHAR(50) NOT NULL,
    "mask_pattern" VARCHAR(200),
    "allowed_roles" JSONB NOT NULL DEFAULT '[]',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "description" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "data_masking_rules_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "report_templates" (
    "id" TEXT NOT NULL,
    "template_code" VARCHAR(100) NOT NULL,
    "template_name" VARCHAR(200) NOT NULL,
    "report_type" VARCHAR(50) NOT NULL,
    "description" TEXT,
    "query_config" JSONB NOT NULL,
    "column_config" JSONB NOT NULL,
    "format" VARCHAR(20) NOT NULL DEFAULT 'json',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_by" VARCHAR(36) NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "report_templates_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "report_instances" (
    "id" TEXT NOT NULL,
    "template_id" VARCHAR(36) NOT NULL,
    "project_id" VARCHAR(36),
    "report_name" VARCHAR(300) NOT NULL,
    "parameters" JSONB NOT NULL DEFAULT '{}',
    "file_url" VARCHAR(500),
    "file_size" INTEGER,
    "format" VARCHAR(20) NOT NULL DEFAULT 'json',
    "status" VARCHAR(20) NOT NULL DEFAULT 'completed',
    "generated_by" VARCHAR(36) NOT NULL,
    "generated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "report_instances_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "edit_check_executions" (
    "id" TEXT NOT NULL,
    "rule_id" VARCHAR(36) NOT NULL,
    "project_id" VARCHAR(36) NOT NULL,
    "subject_id" VARCHAR(36) NOT NULL,
    "visit_id" VARCHAR(36),
    "form_id" VARCHAR(36) NOT NULL,
    "field_values" JSONB NOT NULL,
    "result" VARCHAR(20) NOT NULL DEFAULT 'pass',
    "error_message" VARCHAR(500),
    "query_generated" BOOLEAN NOT NULL DEFAULT false,
    "query_id" VARCHAR(36),
    "executed_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "edit_check_executions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "workflow_timeout_configs" (
    "id" TEXT NOT NULL,
    "workflow_type" VARCHAR(50) NOT NULL,
    "stage_index" INTEGER NOT NULL,
    "timeout_hours" INTEGER NOT NULL,
    "reminder_hours" INTEGER NOT NULL DEFAULT 24,
    "escalate_to_role" VARCHAR(50),
    "action_on_timeout" VARCHAR(20) NOT NULL DEFAULT 'notify',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "workflow_timeout_configs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "cdisc_domains" (
    "id" VARCHAR(36) NOT NULL DEFAULT gen_random_uuid(),
    "domain_code" VARCHAR(10) NOT NULL,
    "domain_name" VARCHAR(200) NOT NULL,
    "domain_class" VARCHAR(50),
    "standard_name" VARCHAR(20) DEFAULT 'CDISC',
    "standard_version" VARCHAR(20) DEFAULT '2.1',
    "description" TEXT,
    "is_active" BOOLEAN DEFAULT true,
    "created_at" TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "cdisc_domains_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "cdisc_code_lists" (
    "id" VARCHAR(36) NOT NULL DEFAULT gen_random_uuid(),
    "code_list_oid" VARCHAR(100) NOT NULL,
    "code_list_name" VARCHAR(200) NOT NULL,
    "domain" VARCHAR(10) NOT NULL,
    "data_type" VARCHAR(20) DEFAULT 'text',
    "items" JSON NOT NULL DEFAULT '[]',
    "is_active" BOOLEAN DEFAULT true,
    "created_at" TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "cdisc_code_lists_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "sdtm_export_configs" (
    "id" VARCHAR(36) NOT NULL DEFAULT gen_random_uuid(),
    "project_id" VARCHAR(36) NOT NULL,
    "domain" VARCHAR(10) NOT NULL,
    "sdtm_dataset_name" VARCHAR(10) NOT NULL,
    "form_code_mapping" JSON NOT NULL DEFAULT '{}',
    "field_mappings" JSON NOT NULL DEFAULT '{}',
    "is_active" BOOLEAN DEFAULT true,
    "created_at" TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "sdtm_export_configs_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_username_key" ON "users"("username");

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "roles_role_code_key" ON "roles"("role_code");

-- CreateIndex
CREATE INDEX "user_roles_user_id_idx" ON "user_roles"("user_id");

-- CreateIndex
CREATE INDEX "user_roles_role_id_idx" ON "user_roles"("role_id");

-- CreateIndex
CREATE UNIQUE INDEX "user_roles_user_id_role_id_project_id_site_id_key" ON "user_roles"("user_id", "role_id", "project_id", "site_id");

-- CreateIndex
CREATE UNIQUE INDEX "permissions_permission_code_key" ON "permissions"("permission_code");

-- CreateIndex
CREATE INDEX "role_permissions_role_id_idx" ON "role_permissions"("role_id");

-- CreateIndex
CREATE UNIQUE INDEX "role_permissions_role_id_permission_id_key" ON "role_permissions"("role_id", "permission_id");

-- CreateIndex
CREATE UNIQUE INDEX "organizations_org_code_key" ON "organizations"("org_code");

-- CreateIndex
CREATE INDEX "organizations_org_type_idx" ON "organizations"("org_type");

-- CreateIndex
CREATE INDEX "organizations_status_idx" ON "organizations"("status");

-- CreateIndex
CREATE INDEX "organizations_parent_id_idx" ON "organizations"("parent_id");

-- CreateIndex
CREATE UNIQUE INDEX "projects_project_code_key" ON "projects"("project_code");

-- CreateIndex
CREATE INDEX "projects_status_idx" ON "projects"("status");

-- CreateIndex
CREATE INDEX "milestones_project_id_idx" ON "milestones"("project_id");

-- CreateIndex
CREATE INDEX "sites_project_id_idx" ON "sites"("project_id");

-- CreateIndex
CREATE UNIQUE INDEX "sites_project_id_site_code_key" ON "sites"("project_id", "site_code");

-- CreateIndex
CREATE INDEX "site_staff_site_id_idx" ON "site_staff"("site_id");

-- CreateIndex
CREATE UNIQUE INDEX "site_staff_site_id_user_id_key" ON "site_staff"("site_id", "user_id");

-- CreateIndex
CREATE INDEX "monitoring_plans_project_id_idx" ON "monitoring_plans"("project_id");

-- CreateIndex
CREATE INDEX "monitoring_visits_project_id_idx" ON "monitoring_visits"("project_id");

-- CreateIndex
CREATE INDEX "timesheets_user_id_week_start_date_idx" ON "timesheets"("user_id", "week_start_date");

-- CreateIndex
CREATE INDEX "timesheet_entries_timesheet_id_idx" ON "timesheet_entries"("timesheet_id");

-- CreateIndex
CREATE UNIQUE INDEX "financial_incomes_income_code_key" ON "financial_incomes"("income_code");

-- CreateIndex
CREATE INDEX "financial_incomes_project_id_idx" ON "financial_incomes"("project_id");

-- CreateIndex
CREATE UNIQUE INDEX "financial_expenses_expense_code_key" ON "financial_expenses"("expense_code");

-- CreateIndex
CREATE INDEX "financial_expenses_project_id_idx" ON "financial_expenses"("project_id");

-- CreateIndex
CREATE INDEX "financial_expenses_submitted_by_idx" ON "financial_expenses"("submitted_by");

-- CreateIndex
CREATE INDEX "subjects_project_id_idx" ON "subjects"("project_id");

-- CreateIndex
CREATE INDEX "subjects_enrollment_status_idx" ON "subjects"("enrollment_status");

-- CreateIndex
CREATE UNIQUE INDEX "subjects_project_id_subject_code_key" ON "subjects"("project_id", "subject_code");

-- CreateIndex
CREATE INDEX "visits_project_id_idx" ON "visits"("project_id");

-- CreateIndex
CREATE INDEX "visits_subject_id_idx" ON "visits"("subject_id");

-- CreateIndex
CREATE UNIQUE INDEX "edc_templates_template_code_key" ON "edc_templates"("template_code");

-- CreateIndex
CREATE INDEX "edc_templates_template_type_idx" ON "edc_templates"("template_type");

-- CreateIndex
CREATE INDEX "crf_data_subject_id_form_code_idx" ON "crf_data"("subject_id", "form_code");

-- CreateIndex
CREATE INDEX "crf_data_cdisc_domain_cdash_variable_idx" ON "crf_data"("cdisc_domain", "cdash_variable");

-- CreateIndex
CREATE INDEX "crf_data_entered_by_idx" ON "crf_data"("entered_by");

-- CreateIndex
CREATE INDEX "crf_data_history_crf_data_id_idx" ON "crf_data_history"("crf_data_id");

-- CreateIndex
CREATE INDEX "data_queries_project_id_idx" ON "data_queries"("project_id");

-- CreateIndex
CREATE INDEX "data_queries_status_idx" ON "data_queries"("status");

-- CreateIndex
CREATE INDEX "data_queries_assigned_to_idx" ON "data_queries"("assigned_to");

-- CreateIndex
CREATE INDEX "data_query_histories_query_id_idx" ON "data_query_histories"("query_id");

-- CreateIndex
CREATE UNIQUE INDEX "edc_randomization_records_subject_id_key" ON "edc_randomization_records"("subject_id");

-- CreateIndex
CREATE UNIQUE INDEX "edc_randomization_records_randomization_number_key" ON "edc_randomization_records"("randomization_number");

-- CreateIndex
CREATE INDEX "edc_randomization_records_project_id_idx" ON "edc_randomization_records"("project_id");

-- CreateIndex
CREATE INDEX "edc_lock_records_project_id_idx" ON "edc_lock_records"("project_id");

-- CreateIndex
CREATE INDEX "edc_lock_records_status_idx" ON "edc_lock_records"("status");

-- CreateIndex
CREATE UNIQUE INDEX "workflow_definitions_workflow_code_key" ON "workflow_definitions"("workflow_code");

-- CreateIndex
CREATE INDEX "workflow_instances_status_idx" ON "workflow_instances"("status");

-- CreateIndex
CREATE INDEX "workflow_instances_initiator_id_idx" ON "workflow_instances"("initiator_id");

-- CreateIndex
CREATE INDEX "workflow_tasks_assigned_to_status_idx" ON "workflow_tasks"("assigned_to", "status");

-- CreateIndex
CREATE INDEX "workflow_tasks_instance_id_idx" ON "workflow_tasks"("instance_id");

-- CreateIndex
CREATE INDEX "unified_audit_logs_system_code_idx" ON "unified_audit_logs"("system_code");

-- CreateIndex
CREATE INDEX "unified_audit_logs_project_id_idx" ON "unified_audit_logs"("project_id");

-- CreateIndex
CREATE INDEX "unified_audit_logs_user_id_idx" ON "unified_audit_logs"("user_id");

-- CreateIndex
CREATE INDEX "unified_audit_logs_event_timestamp_idx" ON "unified_audit_logs"("event_timestamp");

-- CreateIndex
CREATE INDEX "unified_audit_logs_table_name_record_id_idx" ON "unified_audit_logs"("table_name", "record_id");

-- CreateIndex
CREATE INDEX "notifications_recipient_id_status_idx" ON "notifications"("recipient_id", "status");

-- CreateIndex
CREATE INDEX "crf_forms_cdisc_domain_idx" ON "crf_forms"("cdisc_domain");

-- CreateIndex
CREATE INDEX "crf_forms_project_id_idx" ON "crf_forms"("project_id");

-- CreateIndex
CREATE INDEX "crf_forms_status_idx" ON "crf_forms"("status");

-- CreateIndex
CREATE UNIQUE INDEX "crf_forms_project_id_form_code_key" ON "crf_forms"("project_id", "form_code");

-- CreateIndex
CREATE INDEX "crf_form_fields_cdisc_domain_cdash_variable_idx" ON "crf_form_fields"("cdisc_domain", "cdash_variable");

-- CreateIndex
CREATE INDEX "crf_form_fields_code_list_oid_idx" ON "crf_form_fields"("code_list_oid");

-- CreateIndex
CREATE INDEX "crf_form_fields_form_id_idx" ON "crf_form_fields"("form_id");

-- CreateIndex
CREATE UNIQUE INDEX "crf_form_fields_form_id_field_code_key" ON "crf_form_fields"("form_id", "field_code");

-- CreateIndex
CREATE INDEX "crf_edit_check_rules_form_id_idx" ON "crf_edit_check_rules"("form_id");

-- CreateIndex
CREATE UNIQUE INDEX "crf_edit_check_rules_form_id_rule_code_key" ON "crf_edit_check_rules"("form_id", "rule_code");

-- CreateIndex
CREATE INDEX "crf_form_versions_form_id_idx" ON "crf_form_versions"("form_id");

-- CreateIndex
CREATE UNIQUE INDEX "crf_form_versions_form_id_version_key" ON "crf_form_versions"("form_id", "version");

-- CreateIndex
CREATE INDEX "crf_form_publications_form_id_idx" ON "crf_form_publications"("form_id");

-- CreateIndex
CREATE INDEX "drugs_project_id_idx" ON "drugs"("project_id");

-- CreateIndex
CREATE UNIQUE INDEX "drugs_project_id_drug_code_key" ON "drugs"("project_id", "drug_code");

-- CreateIndex
CREATE INDEX "drug_supply_plans_drug_id_idx" ON "drug_supply_plans"("drug_id");

-- CreateIndex
CREATE UNIQUE INDEX "drug_shipments_shipment_code_key" ON "drug_shipments"("shipment_code");

-- CreateIndex
CREATE INDEX "drug_shipments_drug_id_idx" ON "drug_shipments"("drug_id");

-- CreateIndex
CREATE INDEX "drug_shipments_status_idx" ON "drug_shipments"("status");

-- CreateIndex
CREATE INDEX "drug_inventories_drug_id_idx" ON "drug_inventories"("drug_id");

-- CreateIndex
CREATE INDEX "drug_inventories_site_id_idx" ON "drug_inventories"("site_id");

-- CreateIndex
CREATE INDEX "drug_destructions_drug_id_idx" ON "drug_destructions"("drug_id");

-- CreateIndex
CREATE INDEX "tmf_documents_project_id_idx" ON "tmf_documents"("project_id");

-- CreateIndex
CREATE INDEX "tmf_documents_tmf_section_idx" ON "tmf_documents"("tmf_section");

-- CreateIndex
CREATE INDEX "tmf_documents_status_idx" ON "tmf_documents"("status");

-- CreateIndex
CREATE UNIQUE INDEX "tmf_documents_project_id_document_code_key" ON "tmf_documents"("project_id", "document_code");

-- CreateIndex
CREATE INDEX "tmf_document_versions_document_id_idx" ON "tmf_document_versions"("document_id");

-- CreateIndex
CREATE UNIQUE INDEX "tmf_document_versions_document_id_version_key" ON "tmf_document_versions"("document_id", "version");

-- CreateIndex
CREATE INDEX "sdv_records_project_id_idx" ON "sdv_records"("project_id");

-- CreateIndex
CREATE INDEX "sdv_records_site_id_idx" ON "sdv_records"("site_id");

-- CreateIndex
CREATE INDEX "sdv_records_subject_id_idx" ON "sdv_records"("subject_id");

-- CreateIndex
CREATE INDEX "sdv_records_cra_user_id_idx" ON "sdv_records"("cra_user_id");

-- CreateIndex
CREATE INDEX "sdv_items_sdv_record_id_idx" ON "sdv_items"("sdv_record_id");

-- CreateIndex
CREATE UNIQUE INDEX "adverse_events_report_code_key" ON "adverse_events"("report_code");

-- CreateIndex
CREATE INDEX "adverse_events_project_id_idx" ON "adverse_events"("project_id");

-- CreateIndex
CREATE INDEX "adverse_events_subject_id_idx" ON "adverse_events"("subject_id");

-- CreateIndex
CREATE INDEX "adverse_events_event_type_idx" ON "adverse_events"("event_type");

-- CreateIndex
CREATE INDEX "adverse_events_status_idx" ON "adverse_events"("status");

-- CreateIndex
CREATE INDEX "sae_reports_adverse_event_id_idx" ON "sae_reports"("adverse_event_id");

-- CreateIndex
CREATE INDEX "sae_reports_report_type_idx" ON "sae_reports"("report_type");

-- CreateIndex
CREATE INDEX "sae_reports_status_idx" ON "sae_reports"("status");

-- CreateIndex
CREATE INDEX "ai_agent_logs_agent_type_idx" ON "ai_agent_logs"("agent_type");

-- CreateIndex
CREATE INDEX "ai_agent_logs_project_id_idx" ON "ai_agent_logs"("project_id");

-- CreateIndex
CREATE INDEX "ai_agent_logs_user_id_idx" ON "ai_agent_logs"("user_id");

-- CreateIndex
CREATE INDEX "ai_agent_logs_created_at_idx" ON "ai_agent_logs"("created_at");

-- CreateIndex
CREATE UNIQUE INDEX "system_configs_config_key_key" ON "system_configs"("config_key");

-- CreateIndex
CREATE UNIQUE INDEX "vendors_vendor_code_key" ON "vendors"("vendor_code");

-- CreateIndex
CREATE INDEX "vendors_vendor_type_idx" ON "vendors"("vendor_type");

-- CreateIndex
CREATE INDEX "vendors_status_idx" ON "vendors"("status");

-- CreateIndex
CREATE UNIQUE INDEX "contracts_contract_code_key" ON "contracts"("contract_code");

-- CreateIndex
CREATE INDEX "contracts_project_id_idx" ON "contracts"("project_id");

-- CreateIndex
CREATE INDEX "contracts_vendor_id_idx" ON "contracts"("vendor_id");

-- CreateIndex
CREATE INDEX "contracts_sign_status_idx" ON "contracts"("sign_status");

-- CreateIndex
CREATE INDEX "ethics_approvals_project_id_idx" ON "ethics_approvals"("project_id");

-- CreateIndex
CREATE INDEX "ethics_approvals_site_id_idx" ON "ethics_approvals"("site_id");

-- CreateIndex
CREATE INDEX "ethics_approvals_approval_status_idx" ON "ethics_approvals"("approval_status");

-- CreateIndex
CREATE INDEX "data_sync_logs_sync_type_idx" ON "data_sync_logs"("sync_type");

-- CreateIndex
CREATE INDEX "data_sync_logs_project_id_idx" ON "data_sync_logs"("project_id");

-- CreateIndex
CREATE INDEX "data_sync_logs_status_idx" ON "data_sync_logs"("status");

-- CreateIndex
CREATE INDEX "data_sync_logs_created_at_idx" ON "data_sync_logs"("created_at");

-- CreateIndex
CREATE INDEX "query_histories_query_id_idx" ON "query_histories"("query_id");

-- CreateIndex
CREATE INDEX "wechat_user_bindings_open_id_idx" ON "wechat_user_bindings"("open_id");

-- CreateIndex
CREATE UNIQUE INDEX "wechat_user_bindings_user_id_channel_key" ON "wechat_user_bindings"("user_id", "channel");

-- CreateIndex
CREATE INDEX "consent_records_project_id_idx" ON "consent_records"("project_id");

-- CreateIndex
CREATE INDEX "consent_records_site_id_idx" ON "consent_records"("site_id");

-- CreateIndex
CREATE INDEX "consent_records_subject_id_idx" ON "consent_records"("subject_id");

-- CreateIndex
CREATE UNIQUE INDEX "abac_policies_policy_code_key" ON "abac_policies"("policy_code");

-- CreateIndex
CREATE INDEX "signature_records_user_id_idx" ON "signature_records"("user_id");

-- CreateIndex
CREATE INDEX "signature_records_project_id_idx" ON "signature_records"("project_id");

-- CreateIndex
CREATE INDEX "signature_records_table_name_record_id_idx" ON "signature_records"("table_name", "record_id");

-- CreateIndex
CREATE INDEX "data_masking_rules_table_name_field_name_idx" ON "data_masking_rules"("table_name", "field_name");

-- CreateIndex
CREATE UNIQUE INDEX "report_templates_template_code_key" ON "report_templates"("template_code");

-- CreateIndex
CREATE INDEX "report_templates_report_type_idx" ON "report_templates"("report_type");

-- CreateIndex
CREATE INDEX "report_instances_template_id_idx" ON "report_instances"("template_id");

-- CreateIndex
CREATE INDEX "report_instances_project_id_idx" ON "report_instances"("project_id");

-- CreateIndex
CREATE INDEX "edit_check_executions_rule_id_idx" ON "edit_check_executions"("rule_id");

-- CreateIndex
CREATE INDEX "edit_check_executions_project_id_idx" ON "edit_check_executions"("project_id");

-- CreateIndex
CREATE INDEX "edit_check_executions_subject_id_idx" ON "edit_check_executions"("subject_id");

-- CreateIndex
CREATE UNIQUE INDEX "workflow_timeout_configs_workflow_type_stage_index_key" ON "workflow_timeout_configs"("workflow_type", "stage_index");

-- CreateIndex
CREATE UNIQUE INDEX "cdisc_domains_domain_code_key" ON "cdisc_domains"("domain_code");

-- CreateIndex
CREATE UNIQUE INDEX "cdisc_code_lists_code_list_oid_key" ON "cdisc_code_lists"("code_list_oid");

-- CreateIndex
CREATE INDEX "idx_cdisc_code_lists_domain" ON "cdisc_code_lists"("domain");

-- CreateIndex
CREATE INDEX "idx_sdtm_export_configs_project" ON "sdtm_export_configs"("project_id");

-- CreateIndex
CREATE UNIQUE INDEX "sdtm_export_configs_project_id_domain_key" ON "sdtm_export_configs"("project_id", "domain");

-- AddForeignKey
ALTER TABLE "user_roles" ADD CONSTRAINT "user_roles_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "roles"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_roles" ADD CONSTRAINT "user_roles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "role_permissions" ADD CONSTRAINT "role_permissions_permission_id_fkey" FOREIGN KEY ("permission_id") REFERENCES "permissions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "role_permissions" ADD CONSTRAINT "role_permissions_role_id_fkey" FOREIGN KEY ("role_id") REFERENCES "roles"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "milestones" ADD CONSTRAINT "milestones_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "sites" ADD CONSTRAINT "sites_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "site_staff" ADD CONSTRAINT "site_staff_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "sites"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "site_staff" ADD CONSTRAINT "site_staff_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "monitoring_plans" ADD CONSTRAINT "monitoring_plans_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "monitoring_visits" ADD CONSTRAINT "monitoring_visits_plan_id_fkey" FOREIGN KEY ("plan_id") REFERENCES "monitoring_plans"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "monitoring_visits" ADD CONSTRAINT "monitoring_visits_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "monitoring_visits" ADD CONSTRAINT "monitoring_visits_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "sites"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "timesheet_entries" ADD CONSTRAINT "timesheet_entries_timesheet_id_fkey" FOREIGN KEY ("timesheet_id") REFERENCES "timesheets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "subjects" ADD CONSTRAINT "subjects_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "subjects" ADD CONSTRAINT "subjects_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "sites"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "visits" ADD CONSTRAINT "visits_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "visits" ADD CONSTRAINT "visits_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "sites"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "visits" ADD CONSTRAINT "visits_subject_id_fkey" FOREIGN KEY ("subject_id") REFERENCES "subjects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "edc_templates" ADD CONSTRAINT "edc_templates_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crf_data" ADD CONSTRAINT "crf_data_subject_id_fkey" FOREIGN KEY ("subject_id") REFERENCES "subjects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crf_data_history" ADD CONSTRAINT "crf_data_history_crf_data_id_fkey" FOREIGN KEY ("crf_data_id") REFERENCES "crf_data"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "data_queries" ADD CONSTRAINT "data_queries_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "data_queries" ADD CONSTRAINT "data_queries_subject_id_fkey" FOREIGN KEY ("subject_id") REFERENCES "subjects"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "data_query_histories" ADD CONSTRAINT "data_query_histories_query_id_fkey" FOREIGN KEY ("query_id") REFERENCES "data_queries"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "edc_randomization_records" ADD CONSTRAINT "edc_randomization_records_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "edc_randomization_records" ADD CONSTRAINT "edc_randomization_records_subject_id_fkey" FOREIGN KEY ("subject_id") REFERENCES "subjects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "edc_lock_records" ADD CONSTRAINT "edc_lock_records_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "workflow_instances" ADD CONSTRAINT "workflow_instances_definition_id_fkey" FOREIGN KEY ("definition_id") REFERENCES "workflow_definitions"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "workflow_tasks" ADD CONSTRAINT "workflow_tasks_instance_id_fkey" FOREIGN KEY ("instance_id") REFERENCES "workflow_instances"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "unified_audit_logs" ADD CONSTRAINT "unified_audit_logs_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "unified_audit_logs" ADD CONSTRAINT "unified_audit_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "notifications" ADD CONSTRAINT "notifications_recipient_id_fkey" FOREIGN KEY ("recipient_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crf_forms" ADD CONSTRAINT "crf_forms_cdisc_domain_fkey" FOREIGN KEY ("cdisc_domain") REFERENCES "cdisc_domains"("domain_code") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crf_forms" ADD CONSTRAINT "crf_forms_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crf_form_fields" ADD CONSTRAINT "crf_form_fields_form_id_fkey" FOREIGN KEY ("form_id") REFERENCES "crf_forms"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crf_form_fields" ADD CONSTRAINT "crf_form_fields_code_list_oid_fkey" FOREIGN KEY ("code_list_oid") REFERENCES "cdisc_code_lists"("code_list_oid") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crf_form_fields" ADD CONSTRAINT "crf_form_fields_cdisc_domain_fkey" FOREIGN KEY ("cdisc_domain") REFERENCES "cdisc_domains"("domain_code") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crf_edit_check_rules" ADD CONSTRAINT "crf_edit_check_rules_form_id_fkey" FOREIGN KEY ("form_id") REFERENCES "crf_forms"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "drugs" ADD CONSTRAINT "drugs_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "drug_supply_plans" ADD CONSTRAINT "drug_supply_plans_drug_id_fkey" FOREIGN KEY ("drug_id") REFERENCES "drugs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "drug_shipments" ADD CONSTRAINT "drug_shipments_drug_id_fkey" FOREIGN KEY ("drug_id") REFERENCES "drugs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "drug_inventories" ADD CONSTRAINT "drug_inventories_drug_id_fkey" FOREIGN KEY ("drug_id") REFERENCES "drugs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "tmf_documents" ADD CONSTRAINT "tmf_documents_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "tmf_document_versions" ADD CONSTRAINT "tmf_document_versions_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "tmf_documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "sdv_items" ADD CONSTRAINT "sdv_items_sdv_record_id_fkey" FOREIGN KEY ("sdv_record_id") REFERENCES "sdv_records"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "sae_reports" ADD CONSTRAINT "sae_reports_adverse_event_id_fkey" FOREIGN KEY ("adverse_event_id") REFERENCES "adverse_events"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "contracts" ADD CONSTRAINT "contracts_vendor_id_fkey" FOREIGN KEY ("vendor_id") REFERENCES "vendors"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ethics_approvals" ADD CONSTRAINT "ethics_approvals_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ethics_approvals" ADD CONSTRAINT "ethics_approvals_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "sites"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "data_sync_logs" ADD CONSTRAINT "data_sync_logs_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "wechat_user_bindings" ADD CONSTRAINT "wechat_user_bindings_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "consent_records" ADD CONSTRAINT "consent_records_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "consent_records" ADD CONSTRAINT "consent_records_site_id_fkey" FOREIGN KEY ("site_id") REFERENCES "sites"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "signature_records" ADD CONSTRAINT "signature_records_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "report_instances" ADD CONSTRAINT "report_instances_template_id_fkey" FOREIGN KEY ("template_id") REFERENCES "report_templates"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "edit_check_executions" ADD CONSTRAINT "edit_check_executions_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "edit_check_executions" ADD CONSTRAINT "edit_check_executions_rule_id_fkey" FOREIGN KEY ("rule_id") REFERENCES "crf_edit_check_rules"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "cdisc_code_lists" ADD CONSTRAINT "cdisc_code_lists_domain_fkey" FOREIGN KEY ("domain") REFERENCES "cdisc_domains"("domain_code") ON DELETE RESTRICT ON UPDATE CASCADE;



-- Seed CDISC Domains
INSERT INTO "cdisc_domains" ("domain_code", "domain_name", "domain_class", "description") VALUES
  ('DM', 'Demographics', 'Special Purpose', '受试者人口学信息'),
  ('CO', 'Comments', 'Special Purpose', '注释'),
  ('SE', 'Subject Elements', 'Special Purpose', '受试者试验阶段'),
  ('SV', 'Subject Visits', 'Special Purpose', '受试者访视'),
  ('CM', 'Concomitant Medications', 'Interventions', '合并用药'),
  ('EX', 'Exposure', 'Interventions', '暴露/给药'),
  ('SU', 'Substance Use', 'Interventions', '物质使用(烟/酒/咖啡等)'),
  ('PR', 'Procedures', 'Interventions', '医疗操作/手术'),
  ('AE', 'Adverse Events', 'Events', '不良事件'),
  ('CE', 'Clinical Events', 'Events', '临床事件'),
  ('DS', 'Disposition', 'Events', '受试者处置/脱落'),
  ('MH', 'Medical History', 'Events', '既往病史'),
  ('DV', 'Protocol Deviations', 'Events', '方案违背'),
  ('HO', 'Healthcare Encounters', 'Events', '医疗接触/住院'),
  ('VS', 'Vital Signs', 'Findings', '生命体征'),
  ('LB', 'Laboratory Test Results', 'Findings', '实验室检查'),
  ('EG', 'ECG Test Results', 'Findings', '心电图检查'),
  ('PE', 'Physical Examination', 'Findings', '体格检查'),
  ('QS', 'Questionnaires', 'Findings', '量表/问卷'),
  ('DA', 'Drug Accountability', 'Findings', '药物清点'),
  ('IE', 'Inclusion/Exclusion Criteria', 'Findings', '入排标准'),
  ('MB', 'Microbiology Specimen', 'Findings', '微生物标本'),
  ('MS', 'Microbiology Susceptibility', 'Findings', '微生物药敏'),
  ('PC', 'Pharmacokinetics Concentrations', 'Findings', '药代动力学浓度'),
  ('PP', 'Pharmacokinetics Parameters', 'Findings', '药代动力学参数'),
  ('SC', 'Subject Characteristics', 'Findings', '受试者特征'),
  ('TU', 'Tumor Identification', 'Findings', '肿瘤识别'),
  ('TR', 'Tumor Results', 'Findings', '肿瘤评估结果'),
  ('RS', 'Disease Response', 'Findings', '疾病缓解评估'),
  ('UR', 'Urinalysis', 'Findings', '尿液分析')
ON CONFLICT ("domain_code") DO NOTHING;

-- Seed System EDC Templates (CDASH / SDTM Aligned)
INSERT INTO "edc_templates" ("id", "template_code", "template_name", "template_type", "version", "is_system_template", "is_shared", "template_data", "status", "published_at") VALUES
  ('sys-tpl-vital-001', 'TPL-VITAL-001', '生命体征记录表', 'vital_signs', '1.0', true, true, '{"fields":[{"id":"SYSBP","max":200,"min":60,"type":"number","label":"收缩压(mmHg)","required":true},{"id":"DIABP","max":130,"min":40,"type":"number","label":"舒张压(mmHg)","required":true},{"id":"HR","max":180,"min":40,"type":"number","label":"心率(次/分)","required":true},{"id":"TEMP","max":42,"min":35,"type":"number","label":"体温(℃)","required":true},{"id":"WEIGHT","max":200,"min":30,"type":"number","label":"体重(kg)","required":true}]}', 'published', CURRENT_TIMESTAMP),
  ('sys-tpl-hba1c-001', 'TPL-HBA1C-001', '糖化血红蛋白检测表', 'lab_result', '1.0', true, true, '{"fields":[{"id":"HBA1C","max":16,"min":4,"type":"number","label":"HbA1c(%)","required":true},{"id":"GLUC","max":30,"min":2,"type":"number","label":"空腹血糖(mmol/L)","required":true},{"id":"LBDAT","type":"date","label":"检测日期","required":true},{"id":"LBNAM","type":"text","label":"检测机构","required":true}]}', 'published', CURRENT_TIMESTAMP),
  ('sys-tpl-ae-001', 'TPL-AE-001', '不良事件记录表', 'ae_report', '2.0', true, true, '{"fields":[{"id":"AETERM","type":"text","label":"不良事件术语","required":true},{"id":"AESTDAT","type":"datetime","label":"发生日期","required":true},{"id":"AESEV","type":"select","label":"严重程度","options":["轻度","中度","重度"],"required":true},{"id":"AEREL","type":"select","label":"因果关系","options":["无关","可能无关","可能有关","很可能有关","肯定有关"],"required":true},{"id":"AEOUT","type":"select","label":"结局","options":["痊愈","好转中","未痊愈","死亡","不明"],"required":true}]}', 'published', CURRENT_TIMESTAMP)
ON CONFLICT ("template_code") DO NOTHING;
