-- ================================================================
-- CTMS Pro 数据库初始化脚本
-- 临床试验管理系统 (Clinical Trial Management System)
-- (基于本地数据库 pg_dump 自动生成)
-- ================================================================

-- 启用核心扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

--
-- PostgreSQL database dump
--


-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: adverse_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.adverse_events (
    id uuid NOT NULL,
    ae_no character varying(50) NOT NULL,
    patient_id uuid,
    trial_id uuid,
    visit_id uuid,
    description text NOT NULL,
    meddra_pt character varying(200),
    meddra_soc character varying(200),
    icd_code character varying(20),
    severity character varying(20),
    is_serious boolean,
    sae_criteria jsonb,
    relatedness character varying(30),
    onset_date date,
    resolution_date date,
    outcome character varying(30),
    action_taken character varying(50),
    treatment text,
    report_status character varying(20),
    reported_to_sponsor boolean,
    sponsor_report_date date,
    reported_to_ethics boolean,
    ethics_report_date date,
    expedited_report boolean,
    reported_by uuid,
    reviewed_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id bigint NOT NULL,
    event_id uuid,
    user_id uuid,
    username character varying(100),
    user_role character varying(50),
    request_id character varying(50),
    ip_address character varying(45),
    user_agent character varying(500),
    action character varying(100) NOT NULL,
    module character varying(50),
    resource_type character varying(100),
    resource_id character varying(100),
    resource_name character varying(300),
    old_values jsonb,
    new_values jsonb,
    success boolean,
    error_message text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: contracts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contracts (
    id uuid NOT NULL,
    contract_no character varying(100) NOT NULL,
    trial_id uuid,
    site_id uuid,
    title character varying(200) NOT NULL,
    contract_type character varying(50),
    party_name character varying(200),
    total_amount numeric(15,2),
    currency character varying(10),
    sign_date date,
    start_date date,
    end_date date,
    status character varying(20),
    payment_terms text,
    doc_id uuid,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id uuid NOT NULL,
    trial_id uuid,
    folder_id uuid,
    site_id uuid,
    title character varying(300) NOT NULL,
    doc_type character varying(100),
    file_name character varying(300),
    file_path character varying(500),
    file_size bigint,
    mime_type character varying(100),
    checksum character varying(64),
    version character varying(20),
    version_notes text,
    previous_id uuid,
    is_current boolean,
    effective_date date,
    expiry_date date,
    requires_esig boolean,
    esig_status character varying(20),
    esig_by uuid,
    esig_at timestamp with time zone,
    esig_cert text,
    status character varying(20),
    reviewed_by uuid,
    approved_by uuid,
    approved_at timestamp with time zone,
    uploaded_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: drug_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.drug_batches (
    id uuid NOT NULL,
    trial_id uuid,
    batch_no character varying(100) NOT NULL,
    drug_name character varying(200) NOT NULL,
    drug_code character varying(100),
    drug_form character varying(50),
    dosage character varying(100),
    manufacturer character varying(200),
    manufacture_date date,
    expiry_date date,
    received_qty integer NOT NULL,
    current_qty integer NOT NULL,
    dispensed_qty integer,
    returned_qty integer,
    destroyed_qty integer,
    unit character varying(20),
    storage_condition character varying(100),
    storage_site uuid,
    current_temp numeric(5,2),
    temp_log jsonb,
    is_blinded boolean,
    unblinding_log jsonb,
    status character varying(20),
    received_by uuid,
    received_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: drug_dispensing; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.drug_dispensing (
    id uuid NOT NULL,
    batch_id uuid,
    patient_id uuid,
    visit_id uuid,
    trial_id uuid,
    dispense_qty integer NOT NULL,
    returned_qty integer,
    randomization_no character varying(50),
    kit_no character varying(100),
    dispensed_by uuid,
    dispensed_at timestamp with time zone DEFAULT now(),
    return_at timestamp with time zone,
    notes text
);


--
-- Name: econsents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.econsents (
    id uuid NOT NULL,
    patient_id uuid,
    trial_id uuid,
    version character varying(20) NOT NULL,
    language character varying(20),
    template_id uuid,
    status character varying(20),
    patient_signature text,
    patient_signed_at timestamp with time zone,
    patient_ip character varying(45),
    patient_cert_fingerprint character varying(255),
    witness_user_id uuid,
    witness_signature text,
    witness_signed_at timestamp with time zone,
    lar_name character varying(100),
    lar_relationship character varying(50),
    lar_signature text,
    lar_signed_at timestamp with time zone,
    gdpr_basis character varying(50),
    data_purposes jsonb,
    withdrawal_at timestamp with time zone,
    doc_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: etmf_folders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.etmf_folders (
    id uuid NOT NULL,
    trial_id uuid,
    parent_id uuid,
    code character varying(50) NOT NULL,
    name character varying(200) NOT NULL,
    section character varying(10),
    is_required boolean,
    sort_order integer,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: monitoring_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.monitoring_reports (
    id uuid NOT NULL,
    report_no character varying(50) NOT NULL,
    trial_id uuid,
    site_id uuid,
    monitor_user_id uuid,
    visit_type character varying(30),
    visit_date date,
    report_date date,
    overall_rating character varying(20),
    findings jsonb,
    actions jsonb,
    status character varying(20),
    approved_by uuid,
    approved_at timestamp with time zone,
    doc_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id uuid NOT NULL,
    user_id uuid,
    trial_id uuid,
    type character varying(50),
    priority character varying(20),
    title character varying(300) NOT NULL,
    content text,
    data jsonb,
    is_read boolean,
    read_at timestamp with time zone,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    id uuid NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(200) NOT NULL,
    type character varying(50),
    address text,
    city character varying(100),
    country character varying(100),
    phone character varying(50),
    email character varying(255),
    license_no character varying(100),
    gcp_certified boolean,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: patient_visits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.patient_visits (
    id uuid NOT NULL,
    patient_id uuid,
    trial_id uuid,
    schedule_id uuid,
    visit_name character varying(100),
    planned_date date,
    actual_date date,
    status character varying(20),
    visit_type character varying(30),
    site_id uuid,
    investigator_id uuid,
    is_protocol_deviation boolean,
    deviation_type character varying(50),
    deviation_notes text,
    assessments jsonb,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: patients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.patients (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    patient_no character varying(50),
    screening_no character varying(50),
    full_name_enc bytea,
    id_card_enc bytea,
    phone_enc bytea,
    email_enc bytea,
    gender character varying(10),
    birth_year integer,
    age integer,
    blood_type character varying(5),
    ethnicity character varying(50),
    diagnosis text,
    icd_code character varying(20),
    disease_stage character varying(50),
    comorbidities jsonb,
    status character varying(30),
    trial_id uuid,
    site_id uuid,
    assigned_to uuid,
    consent_given boolean,
    consent_date timestamp with time zone,
    consent_doc_id uuid,
    gdpr_log jsonb,
    emr_patient_id character varying(100),
    hl7_fhir_id character varying(100),
    screening_date date,
    enrollment_date date,
    completion_date date,
    created_by uuid,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    arm character varying(50)
);


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    id uuid NOT NULL,
    contract_id uuid,
    trial_id uuid,
    payment_type character varying(50),
    description text,
    planned_amount numeric(15,2),
    actual_amount numeric(15,2),
    planned_date date,
    actual_date date,
    status character varying(20),
    invoice_no character varying(100),
    invoice_date date,
    invoice_amount numeric(15,2),
    notes text,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: qc_issues; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qc_issues (
    id uuid NOT NULL,
    issue_no character varying(50) NOT NULL,
    trial_id uuid,
    site_id uuid,
    report_id uuid,
    category character varying(50),
    severity character varying(20),
    description text NOT NULL,
    due_date date,
    status character varying(20),
    assigned_to uuid,
    resolution text,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: randomization_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.randomization_codes (
    id uuid NOT NULL,
    scheme_id uuid NOT NULL,
    block_id character varying(50) NOT NULL,
    sequence integer NOT NULL,
    randomization_code character varying(50) NOT NULL,
    treatment_arm character varying(50) NOT NULL,
    treatment_name character varying(100),
    strata_values jsonb,
    is_used boolean,
    used_at timestamp with time zone,
    used_by_subject character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: randomization_schemes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.randomization_schemes (
    id uuid NOT NULL,
    scheme_code character varying(50) NOT NULL,
    scheme_name character varying(200) NOT NULL,
    scheme_type character varying(30) NOT NULL,
    trial_id uuid,
    block_sizes integer[],
    ratio character varying(20),
    strata_factors character varying[],
    arms jsonb,
    total_subjects integer NOT NULL,
    is_blinded boolean,
    blinding_method character varying(20),
    status character varying(20),
    created_by uuid,
    activated_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    permissions jsonb,
    is_system boolean,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: screening_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.screening_records (
    id uuid NOT NULL,
    patient_id uuid,
    trial_id uuid,
    criteria_result jsonb,
    match_score numeric(5,2),
    screen_result character varying(20),
    fail_reason text,
    screened_by uuid,
    screened_at timestamp with time zone DEFAULT now()
);


--
-- Name: sites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sites (
    id uuid NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(200) NOT NULL,
    organization_id uuid,
    address text,
    pi_name character varying(100),
    pi_user_id uuid,
    contact_phone character varying(50),
    contact_email character varying(255),
    status character varying(20),
    gcp_cert_expiry date,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: subject_randomizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subject_randomizations (
    id uuid NOT NULL,
    scheme_id uuid NOT NULL,
    patient_id uuid NOT NULL,
    subject_code character varying(50) NOT NULL,
    randomization_code character varying(50) NOT NULL,
    block_id character varying(50),
    block_sequence integer,
    treatment_arm character varying(50) NOT NULL,
    treatment_name character varying(100),
    strata_values jsonb,
    is_blinded boolean,
    unblinded_at timestamp with time zone,
    unblinded_by uuid,
    unblind_reason text,
    status character varying(20),
    drug_code character varying(50),
    kit_number character varying(50),
    assigned_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: system_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_config (
    id uuid NOT NULL,
    category character varying(50) NOT NULL,
    key character varying(100) NOT NULL,
    value text,
    description text,
    is_editable boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: timesheets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.timesheets (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    date date NOT NULL,
    project character varying(200) NOT NULL,
    task character varying(200) NOT NULL,
    hours numeric(5,2) NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: token_blacklist; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.token_blacklist (
    id uuid NOT NULL,
    jti character varying(255) NOT NULL,
    user_id uuid,
    expired_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: trial_milestones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trial_milestones (
    id uuid NOT NULL,
    trial_id uuid,
    name character varying(200) NOT NULL,
    milestone_type character varying(50),
    planned_date date,
    actual_date date,
    status character varying(20),
    owner_user_id uuid,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: trial_sites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trial_sites (
    id uuid NOT NULL,
    trial_id uuid,
    site_id uuid,
    status character varying(20),
    target_enrollment integer,
    enrolled_count integer,
    initiation_date date,
    close_date date,
    budget_allocated numeric(15,2),
    budget_spent numeric(15,2),
    pi_user_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: trials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trials (
    id uuid NOT NULL,
    trial_no character varying(50) NOT NULL,
    short_name character varying(100) NOT NULL,
    full_name text NOT NULL,
    phase character varying(10),
    status character varying(30),
    type character varying(50),
    indication text,
    drug_name character varying(200),
    drug_code character varying(100),
    sponsor character varying(200),
    sponsor_contact character varying(100),
    cro character varying(200),
    planned_start date,
    actual_start date,
    planned_end date,
    actual_end date,
    target_enrollment integer,
    enrolled_count integer,
    screened_count integer,
    screen_fail_count integer,
    completed_count integer,
    dropped_count integer,
    total_budget numeric(15,2),
    spent_amount numeric(15,2),
    currency character varying(10),
    protocol_version character varying(20),
    protocol_date date,
    protocol_doc_id uuid,
    ctgov_id character varying(50),
    cde_id character varying(50),
    ethics_approval_no character varying(100),
    pm_user_id uuid,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    employee_id character varying(50),
    username character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(200) NOT NULL,
    phone character varying(20),
    department character varying(100),
    title character varying(100),
    role_id uuid,
    organization_id uuid,
    is_active boolean,
    is_superuser boolean,
    last_login_at timestamp with time zone,
    last_login_ip character varying(45),
    failed_attempts integer,
    locked_until timestamp with time zone,
    mfa_enabled boolean,
    mfa_secret character varying(100),
    data_consent boolean,
    consent_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: visit_schedules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.visit_schedules (
    id uuid NOT NULL,
    trial_id uuid,
    visit_name character varying(100) NOT NULL,
    visit_type character varying(30),
    visit_order integer,
    window_target integer,
    window_minus integer,
    window_plus integer,
    is_mandatory boolean,
    assessment_list jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);


--
-- Name: adverse_events pk_adverse_events; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.adverse_events
    ADD CONSTRAINT pk_adverse_events PRIMARY KEY (id);


--
-- Name: audit_logs pk_audit_logs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT pk_audit_logs PRIMARY KEY (id);


--
-- Name: contracts pk_contracts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT pk_contracts PRIMARY KEY (id);


--
-- Name: documents pk_documents; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT pk_documents PRIMARY KEY (id);


--
-- Name: drug_batches pk_drug_batches; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_batches
    ADD CONSTRAINT pk_drug_batches PRIMARY KEY (id);


--
-- Name: drug_dispensing pk_drug_dispensing; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_dispensing
    ADD CONSTRAINT pk_drug_dispensing PRIMARY KEY (id);


--
-- Name: econsents pk_econsents; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.econsents
    ADD CONSTRAINT pk_econsents PRIMARY KEY (id);


--
-- Name: etmf_folders pk_etmf_folders; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.etmf_folders
    ADD CONSTRAINT pk_etmf_folders PRIMARY KEY (id);


--
-- Name: monitoring_reports pk_monitoring_reports; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring_reports
    ADD CONSTRAINT pk_monitoring_reports PRIMARY KEY (id);


--
-- Name: notifications pk_notifications; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT pk_notifications PRIMARY KEY (id);


--
-- Name: organizations pk_organizations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT pk_organizations PRIMARY KEY (id);


--
-- Name: patient_visits pk_patient_visits; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT pk_patient_visits PRIMARY KEY (id);


--
-- Name: payments pk_payments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT pk_payments PRIMARY KEY (id);


--
-- Name: qc_issues pk_qc_issues; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qc_issues
    ADD CONSTRAINT pk_qc_issues PRIMARY KEY (id);


--
-- Name: randomization_codes pk_randomization_codes; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.randomization_codes
    ADD CONSTRAINT pk_randomization_codes PRIMARY KEY (id);


--
-- Name: randomization_schemes pk_randomization_schemes; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.randomization_schemes
    ADD CONSTRAINT pk_randomization_schemes PRIMARY KEY (id);


--
-- Name: roles pk_roles; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT pk_roles PRIMARY KEY (id);


--
-- Name: screening_records pk_screening_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screening_records
    ADD CONSTRAINT pk_screening_records PRIMARY KEY (id);


--
-- Name: sites pk_sites; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT pk_sites PRIMARY KEY (id);


--
-- Name: subject_randomizations pk_subject_randomizations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subject_randomizations
    ADD CONSTRAINT pk_subject_randomizations PRIMARY KEY (id);


--
-- Name: system_config pk_system_config; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT pk_system_config PRIMARY KEY (id);


--
-- Name: timesheets pk_timesheets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets
    ADD CONSTRAINT pk_timesheets PRIMARY KEY (id);


--
-- Name: token_blacklist pk_token_blacklist; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT pk_token_blacklist PRIMARY KEY (id);


--
-- Name: trial_milestones pk_trial_milestones; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trial_milestones
    ADD CONSTRAINT pk_trial_milestones PRIMARY KEY (id);


--
-- Name: trial_sites pk_trial_sites; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trial_sites
    ADD CONSTRAINT pk_trial_sites PRIMARY KEY (id);


--
-- Name: trials pk_trials; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trials
    ADD CONSTRAINT pk_trials PRIMARY KEY (id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT pk_users PRIMARY KEY (id);


--
-- Name: visit_schedules pk_visit_schedules; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visit_schedules
    ADD CONSTRAINT pk_visit_schedules PRIMARY KEY (id);


--
-- Name: audit_logs uq_audit_logs_event_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT uq_audit_logs_event_id UNIQUE (event_id);


--
-- Name: contracts uq_contracts_contract_no; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT uq_contracts_contract_no UNIQUE (contract_no);


--
-- Name: monitoring_reports uq_monitoring_reports_report_no; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring_reports
    ADD CONSTRAINT uq_monitoring_reports_report_no UNIQUE (report_no);


--
-- Name: organizations uq_organizations_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT uq_organizations_code UNIQUE (code);


--
-- Name: qc_issues uq_qc_issues_issue_no; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qc_issues
    ADD CONSTRAINT uq_qc_issues_issue_no UNIQUE (issue_no);


--
-- Name: randomization_codes uq_randomization_codes_randomization_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.randomization_codes
    ADD CONSTRAINT uq_randomization_codes_randomization_code UNIQUE (randomization_code);


--
-- Name: sites uq_sites_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT uq_sites_code UNIQUE (code);


--
-- Name: subject_randomizations uq_subject_randomizations_randomization_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subject_randomizations
    ADD CONSTRAINT uq_subject_randomizations_randomization_code UNIQUE (randomization_code);


--
-- Name: subject_randomizations uq_subject_randomizations_subject_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subject_randomizations
    ADD CONSTRAINT uq_subject_randomizations_subject_code UNIQUE (subject_code);


--
-- Name: users uq_users_employee_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_employee_id UNIQUE (employee_id);


--
-- Name: ix_adverse_events_ae_no; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_adverse_events_ae_no ON public.adverse_events USING btree (ae_no);


--
-- Name: ix_adverse_events_is_serious; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_adverse_events_is_serious ON public.adverse_events USING btree (is_serious);


--
-- Name: ix_adverse_events_patient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_adverse_events_patient_id ON public.adverse_events USING btree (patient_id);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_drug_batches_batch_no; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_drug_batches_batch_no ON public.drug_batches USING btree (batch_no);


--
-- Name: ix_drug_batches_expiry_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_drug_batches_expiry_date ON public.drug_batches USING btree (expiry_date);


--
-- Name: ix_notifications_is_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: ix_patient_visits_patient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_patient_visits_patient_id ON public.patient_visits USING btree (patient_id);


--
-- Name: ix_randomization_codes_is_used; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_randomization_codes_is_used ON public.randomization_codes USING btree (is_used);


--
-- Name: ix_randomization_codes_scheme_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_randomization_codes_scheme_id ON public.randomization_codes USING btree (scheme_id);


--
-- Name: ix_randomization_schemes_scheme_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_randomization_schemes_scheme_code ON public.randomization_schemes USING btree (scheme_code);


--
-- Name: ix_randomization_schemes_trial_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_randomization_schemes_trial_id ON public.randomization_schemes USING btree (trial_id);


--
-- Name: ix_roles_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_roles_code ON public.roles USING btree (code);


--
-- Name: ix_screening_records_patient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_screening_records_patient_id ON public.screening_records USING btree (patient_id);


--
-- Name: ix_subject_randomizations_patient_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subject_randomizations_patient_id ON public.subject_randomizations USING btree (patient_id);


--
-- Name: ix_subject_randomizations_scheme_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_subject_randomizations_scheme_id ON public.subject_randomizations USING btree (scheme_id);


--
-- Name: ix_token_blacklist_jti; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_token_blacklist_jti ON public.token_blacklist USING btree (jti);


--
-- Name: ix_trials_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trials_status ON public.trials USING btree (status);


--
-- Name: ix_trials_trial_no; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_trials_trial_no ON public.trials USING btree (trial_no);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: adverse_events fk_adverse_events_reported_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.adverse_events
    ADD CONSTRAINT fk_adverse_events_reported_by_users FOREIGN KEY (reported_by) REFERENCES public.users(id);


--
-- Name: adverse_events fk_adverse_events_reviewed_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.adverse_events
    ADD CONSTRAINT fk_adverse_events_reviewed_by_users FOREIGN KEY (reviewed_by) REFERENCES public.users(id);


--
-- Name: adverse_events fk_adverse_events_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.adverse_events
    ADD CONSTRAINT fk_adverse_events_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: adverse_events fk_adverse_events_visit_id_patient_visits; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.adverse_events
    ADD CONSTRAINT fk_adverse_events_visit_id_patient_visits FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id);


--
-- Name: audit_logs fk_audit_logs_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT fk_audit_logs_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: contracts fk_contracts_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT fk_contracts_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: contracts fk_contracts_site_id_sites; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT fk_contracts_site_id_sites FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: contracts fk_contracts_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT fk_contracts_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: documents fk_documents_approved_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_approved_by_users FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: documents fk_documents_esig_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_esig_by_users FOREIGN KEY (esig_by) REFERENCES public.users(id);


--
-- Name: documents fk_documents_folder_id_etmf_folders; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_folder_id_etmf_folders FOREIGN KEY (folder_id) REFERENCES public.etmf_folders(id);


--
-- Name: documents fk_documents_previous_id_documents; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_previous_id_documents FOREIGN KEY (previous_id) REFERENCES public.documents(id);


--
-- Name: documents fk_documents_reviewed_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_reviewed_by_users FOREIGN KEY (reviewed_by) REFERENCES public.users(id);


--
-- Name: documents fk_documents_site_id_sites; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_site_id_sites FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: documents fk_documents_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: documents fk_documents_uploaded_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT fk_documents_uploaded_by_users FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


--
-- Name: drug_batches fk_drug_batches_received_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_batches
    ADD CONSTRAINT fk_drug_batches_received_by_users FOREIGN KEY (received_by) REFERENCES public.users(id);


--
-- Name: drug_batches fk_drug_batches_storage_site_sites; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_batches
    ADD CONSTRAINT fk_drug_batches_storage_site_sites FOREIGN KEY (storage_site) REFERENCES public.sites(id);


--
-- Name: drug_batches fk_drug_batches_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_batches
    ADD CONSTRAINT fk_drug_batches_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: drug_dispensing fk_drug_dispensing_batch_id_drug_batches; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_dispensing
    ADD CONSTRAINT fk_drug_dispensing_batch_id_drug_batches FOREIGN KEY (batch_id) REFERENCES public.drug_batches(id);


--
-- Name: drug_dispensing fk_drug_dispensing_dispensed_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_dispensing
    ADD CONSTRAINT fk_drug_dispensing_dispensed_by_users FOREIGN KEY (dispensed_by) REFERENCES public.users(id);


--
-- Name: drug_dispensing fk_drug_dispensing_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_dispensing
    ADD CONSTRAINT fk_drug_dispensing_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: drug_dispensing fk_drug_dispensing_visit_id_patient_visits; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drug_dispensing
    ADD CONSTRAINT fk_drug_dispensing_visit_id_patient_visits FOREIGN KEY (visit_id) REFERENCES public.patient_visits(id);


--
-- Name: econsents fk_econsents_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.econsents
    ADD CONSTRAINT fk_econsents_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: econsents fk_econsents_witness_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.econsents
    ADD CONSTRAINT fk_econsents_witness_user_id_users FOREIGN KEY (witness_user_id) REFERENCES public.users(id);


--
-- Name: etmf_folders fk_etmf_folders_parent_id_etmf_folders; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.etmf_folders
    ADD CONSTRAINT fk_etmf_folders_parent_id_etmf_folders FOREIGN KEY (parent_id) REFERENCES public.etmf_folders(id);


--
-- Name: etmf_folders fk_etmf_folders_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.etmf_folders
    ADD CONSTRAINT fk_etmf_folders_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: monitoring_reports fk_monitoring_reports_approved_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring_reports
    ADD CONSTRAINT fk_monitoring_reports_approved_by_users FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: monitoring_reports fk_monitoring_reports_monitor_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring_reports
    ADD CONSTRAINT fk_monitoring_reports_monitor_user_id_users FOREIGN KEY (monitor_user_id) REFERENCES public.users(id);


--
-- Name: monitoring_reports fk_monitoring_reports_site_id_sites; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring_reports
    ADD CONSTRAINT fk_monitoring_reports_site_id_sites FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: monitoring_reports fk_monitoring_reports_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.monitoring_reports
    ADD CONSTRAINT fk_monitoring_reports_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: notifications fk_notifications_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT fk_notifications_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: notifications fk_notifications_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT fk_notifications_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: patient_visits fk_patient_visits_investigator_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT fk_patient_visits_investigator_id_users FOREIGN KEY (investigator_id) REFERENCES public.users(id);


--
-- Name: patient_visits fk_patient_visits_schedule_id_visit_schedules; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT fk_patient_visits_schedule_id_visit_schedules FOREIGN KEY (schedule_id) REFERENCES public.visit_schedules(id);


--
-- Name: patient_visits fk_patient_visits_site_id_sites; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT fk_patient_visits_site_id_sites FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: patient_visits fk_patient_visits_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.patient_visits
    ADD CONSTRAINT fk_patient_visits_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: payments fk_payments_contract_id_contracts; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT fk_payments_contract_id_contracts FOREIGN KEY (contract_id) REFERENCES public.contracts(id);


--
-- Name: payments fk_payments_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT fk_payments_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: payments fk_payments_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT fk_payments_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: qc_issues fk_qc_issues_assigned_to_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qc_issues
    ADD CONSTRAINT fk_qc_issues_assigned_to_users FOREIGN KEY (assigned_to) REFERENCES public.users(id);


--
-- Name: qc_issues fk_qc_issues_report_id_monitoring_reports; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qc_issues
    ADD CONSTRAINT fk_qc_issues_report_id_monitoring_reports FOREIGN KEY (report_id) REFERENCES public.monitoring_reports(id);


--
-- Name: qc_issues fk_qc_issues_site_id_sites; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qc_issues
    ADD CONSTRAINT fk_qc_issues_site_id_sites FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: qc_issues fk_qc_issues_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qc_issues
    ADD CONSTRAINT fk_qc_issues_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: randomization_codes fk_randomization_codes_scheme_id_randomization_schemes; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.randomization_codes
    ADD CONSTRAINT fk_randomization_codes_scheme_id_randomization_schemes FOREIGN KEY (scheme_id) REFERENCES public.randomization_schemes(id) ON DELETE CASCADE;


--
-- Name: randomization_schemes fk_randomization_schemes_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.randomization_schemes
    ADD CONSTRAINT fk_randomization_schemes_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: randomization_schemes fk_randomization_schemes_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.randomization_schemes
    ADD CONSTRAINT fk_randomization_schemes_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: screening_records fk_screening_records_screened_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screening_records
    ADD CONSTRAINT fk_screening_records_screened_by_users FOREIGN KEY (screened_by) REFERENCES public.users(id);


--
-- Name: screening_records fk_screening_records_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.screening_records
    ADD CONSTRAINT fk_screening_records_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id);


--
-- Name: sites fk_sites_organization_id_organizations; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT fk_sites_organization_id_organizations FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: sites fk_sites_pi_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sites
    ADD CONSTRAINT fk_sites_pi_user_id_users FOREIGN KEY (pi_user_id) REFERENCES public.users(id);


--
-- Name: subject_randomizations fk_subject_randomizations_assigned_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subject_randomizations
    ADD CONSTRAINT fk_subject_randomizations_assigned_by_users FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: subject_randomizations fk_subject_randomizations_scheme_id_randomization_schemes; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subject_randomizations
    ADD CONSTRAINT fk_subject_randomizations_scheme_id_randomization_schemes FOREIGN KEY (scheme_id) REFERENCES public.randomization_schemes(id) ON DELETE CASCADE;


--
-- Name: subject_randomizations fk_subject_randomizations_unblinded_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subject_randomizations
    ADD CONSTRAINT fk_subject_randomizations_unblinded_by_users FOREIGN KEY (unblinded_by) REFERENCES public.users(id);


--
-- Name: timesheets fk_timesheets_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets
    ADD CONSTRAINT fk_timesheets_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: token_blacklist fk_token_blacklist_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT fk_token_blacklist_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: trial_milestones fk_trial_milestones_owner_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trial_milestones
    ADD CONSTRAINT fk_trial_milestones_owner_user_id_users FOREIGN KEY (owner_user_id) REFERENCES public.users(id);


--
-- Name: trial_milestones fk_trial_milestones_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trial_milestones
    ADD CONSTRAINT fk_trial_milestones_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id) ON DELETE CASCADE;


--
-- Name: trial_sites fk_trial_sites_pi_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trial_sites
    ADD CONSTRAINT fk_trial_sites_pi_user_id_users FOREIGN KEY (pi_user_id) REFERENCES public.users(id);


--
-- Name: trial_sites fk_trial_sites_site_id_sites; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trial_sites
    ADD CONSTRAINT fk_trial_sites_site_id_sites FOREIGN KEY (site_id) REFERENCES public.sites(id);


--
-- Name: trial_sites fk_trial_sites_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trial_sites
    ADD CONSTRAINT fk_trial_sites_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id) ON DELETE CASCADE;


--
-- Name: trials fk_trials_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trials
    ADD CONSTRAINT fk_trials_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: trials fk_trials_pm_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trials
    ADD CONSTRAINT fk_trials_pm_user_id_users FOREIGN KEY (pm_user_id) REFERENCES public.users(id);


--
-- Name: users fk_users_organization_id_organizations; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_organization_id_organizations FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: users fk_users_role_id_roles; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_role_id_roles FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: visit_schedules fk_visit_schedules_trial_id_trials; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visit_schedules
    ADD CONSTRAINT fk_visit_schedules_trial_id_trials FOREIGN KEY (trial_id) REFERENCES public.trials(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict gvTXDO35qUsTzPkHzrC5dO6KM8tmTT74RE3L44OEiM2XavEKdTwX0heaLBxQTuJ

