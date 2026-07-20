<<<<<<< HEAD
"""
SQLAlchemy ORM 模型定义
所有数据表对应的 Python 类
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Date,
    DateTime, Numeric, BigInteger, ForeignKey, JSON,
    LargeBinary, ARRAY
)
from sqlalchemy.dialects.postgresql import INET, UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class TimestampMixin:
    """时间戳公共字段"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── 角色与用户 ────────────────────────────────────────────────────

class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code        = Column(String(50), unique=True, nullable=False, index=True)
    name        = Column(String(100), nullable=False)
    description = Column(Text)
    permissions = Column(JSONB, default=list)
    is_system   = Column(Boolean, default=False)

    users = relationship("User", back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id     = Column(String(50), unique=True)
    username        = Column(String(100), unique=True, nullable=False, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(200), nullable=False)
    phone           = Column(String(20))
    department      = Column(String(100))
    title           = Column(String(100))
    role_id         = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    is_active       = Column(Boolean, default=True)
    is_superuser    = Column(Boolean, default=False)
    last_login_at   = Column(DateTime(timezone=True))
    last_login_ip   = Column(INET)
    failed_attempts = Column(Integer, default=0)
    locked_until    = Column(DateTime(timezone=True))
    mfa_enabled     = Column(Boolean, default=False)
    mfa_secret      = Column(String(100))
    data_consent    = Column(Boolean, default=False)
    consent_at      = Column(DateTime(timezone=True))

    role = relationship("Role", back_populates="users")
    organization = relationship("Organization", back_populates="users")


class Timesheet(Base, TimestampMixin):
    __tablename__ = "timesheets"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date        = Column(Date, nullable=False)
    project     = Column(String(200), nullable=False)
    task        = Column(String(200), nullable=False)
    hours       = Column(Numeric(5, 2), nullable=False)
    notes       = Column(Text)

    user = relationship("User")


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti        = Column(String(255), unique=True, nullable=False, index=True)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    expired_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── 机构与中心 ────────────────────────────────────────────────────

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code          = Column(String(50), unique=True, nullable=False)
    name          = Column(String(200), nullable=False)
    type          = Column(String(50))
    address       = Column(Text)
    city          = Column(String(100))
    country       = Column(String(100), default="中国")
    phone         = Column(String(50))
    email         = Column(String(255))
    license_no    = Column(String(100))
    gcp_certified = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)

    users = relationship("User", back_populates="organization")
    sites = relationship("Site", back_populates="organization")


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code            = Column(String(50), unique=True, nullable=False)
    name            = Column(String(200), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    address         = Column(Text)
    pi_name         = Column(String(100))
    pi_user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    contact_phone   = Column(String(50))
    contact_email   = Column(String(255))
    status          = Column(String(20), default="ACTIVE")
    gcp_cert_expiry = Column(Date)

    organization = relationship("Organization", back_populates="sites")


# ─── 临床试验 ──────────────────────────────────────────────────────

class Trial(Base, TimestampMixin):
    __tablename__ = "trials"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_no        = Column(String(50), unique=True, nullable=False, index=True)
    short_name      = Column(String(100), nullable=False)
    full_name       = Column(Text, nullable=False)
    phase           = Column(String(10))
    status          = Column(String(30), default="PLANNING", index=True)
    type            = Column(String(50))
    indication      = Column(Text)
    drug_name       = Column(String(200))
    drug_code       = Column(String(100))
    sponsor         = Column(String(200))
    sponsor_contact = Column(String(100))
    cro             = Column(String(200))
    planned_start   = Column(Date)
    actual_start    = Column(Date)
    planned_end     = Column(Date)
    actual_end      = Column(Date)
    target_enrollment   = Column(Integer, default=0)
    enrolled_count      = Column(Integer, default=0)
    screened_count      = Column(Integer, default=0)
    screen_fail_count   = Column(Integer, default=0)
    completed_count     = Column(Integer, default=0)
    dropped_count       = Column(Integer, default=0)
    total_budget        = Column(Numeric(15, 2))
    spent_amount        = Column(Numeric(15, 2), default=0)
    currency            = Column(String(10), default="CNY")
    protocol_version    = Column(String(20))
    protocol_date       = Column(Date)
    protocol_doc_id     = Column(UUID(as_uuid=True))
    ctgov_id            = Column(String(50))
    cde_id             = Column(String(50))
    ethics_approval_no = Column(String(100))
    pm_user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    trial_code         = Column(String(100))

    patients    = relationship("Patient", back_populates="trial")
    milestones  = relationship("TrialMilestone", back_populates="trial")
    trial_sites = relationship("TrialSite", back_populates="trial")
    extension   = relationship("TrialExtension", back_populates="trial", uselist=False, cascade="all, delete-orphan")


class TrialExtension(Base, TimestampMixin):
    __tablename__ = "trial_extensions"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id    = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"), unique=True, index=True)
    extra_data  = Column(JSONB, default=dict)

    trial       = relationship("Trial", back_populates="extension")


class TrialSite(Base, TimestampMixin):
    __tablename__ = "trial_sites"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    status          = Column(String(20), default="INITIATING")
    target_enrollment = Column(Integer, default=0)
    enrolled_count    = Column(Integer, default=0)
    initiation_date   = Column(Date)
    close_date        = Column(Date)
    budget_allocated  = Column(Numeric(15, 2))
    budget_spent      = Column(Numeric(15, 2), default=0)
    pi_user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    trial = relationship("Trial", back_populates="trial_sites")


class TrialMilestone(Base, TimestampMixin):
    __tablename__ = "trial_milestones"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"))
    name            = Column(String(200), nullable=False)
    milestone_type  = Column(String(50))
    planned_date    = Column(Date)
    actual_date     = Column(Date)
    status          = Column(String(20), default="PENDING")
    owner_user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes           = Column(Text)

    trial = relationship("Trial", back_populates="milestones")


# ─── 患者管理 ──────────────────────────────────────────────────────

class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_no      = Column(String(50), unique=True, nullable=False, index=True)
    screening_no    = Column(String(50), index=True)
    full_name_enc   = Column(LargeBinary)       # 加密存储
    id_card_enc     = Column(LargeBinary)
    phone_enc       = Column(LargeBinary)
    email_enc       = Column(LargeBinary)
    gender          = Column(String(10))
    birth_year      = Column(Integer)
    age             = Column(Integer)
    blood_type      = Column(String(5))
    ethnicity       = Column(String(50))
    diagnosis       = Column(Text)
    icd_code        = Column(String(20))
    disease_stage   = Column(String(50))
    comorbidities   = Column(JSONB, default=list)
    status          = Column(String(30), default="SCREENING", index=True)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"), index=True)
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    assigned_to     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    consent_given   = Column(Boolean, default=False)
    consent_date    = Column(DateTime(timezone=True))
    consent_doc_id  = Column(UUID(as_uuid=True))
    gdpr_log        = Column(JSONB, default=list)
    emr_patient_id  = Column(String(100))
    hl7_fhir_id     = Column(String(100))
    screening_date  = Column(Date)
    enrollment_date = Column(Date)
    completion_date = Column(Date)
    arm             = Column(String(50))
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    trial   = relationship("Trial", back_populates="patients")
    visits  = relationship("PatientVisit", back_populates="patient")
    aes     = relationship("AdverseEvent", back_populates="patient")
    econsents = relationship("EConsent", back_populates="patient")


class EConsent(Base, TimestampMixin):
    __tablename__ = "econsents"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"))
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    version         = Column(String(20), nullable=False)
    language        = Column(String(20), default="zh-CN")
    template_id     = Column(UUID(as_uuid=True))
    status          = Column(String(20), default="PENDING")
    patient_signature       = Column(Text)
    patient_signed_at       = Column(DateTime(timezone=True))
    patient_ip              = Column(String(45))
    patient_cert_fingerprint = Column(String(255))
    witness_user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    witness_signature       = Column(Text)
    witness_signed_at       = Column(DateTime(timezone=True))
    lar_name                = Column(String(100))
    lar_relationship        = Column(String(50))
    lar_signature           = Column(Text)
    lar_signed_at           = Column(DateTime(timezone=True))
    gdpr_basis              = Column(String(50), default="CONSENT")
    data_purposes           = Column(JSONB, default=list)
    withdrawal_at           = Column(DateTime(timezone=True))
    doc_id                  = Column(UUID(as_uuid=True))

    patient = relationship("Patient", back_populates="econsents")


# ─── 访视管理 ──────────────────────────────────────────────────────

class VisitSchedule(Base):
    __tablename__ = "visit_schedules"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"))
    visit_name      = Column(String(100), nullable=False)
    visit_type      = Column(String(30))
    visit_order     = Column(Integer)
    window_target   = Column(Integer)
    window_minus    = Column(Integer, default=3)
    window_plus     = Column(Integer, default=3)
    is_mandatory    = Column(Boolean, default=True)
    assessment_list = Column(JSONB, default=list)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class PatientVisit(Base, TimestampMixin):
    __tablename__ = "patient_visits"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id            = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    trial_id              = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    schedule_id           = Column(UUID(as_uuid=True), ForeignKey("visit_schedules.id"))
    visit_name            = Column(String(100))
    planned_date          = Column(Date)
    actual_date           = Column(Date)
    status                = Column(String(20), default="SCHEDULED")
    visit_type            = Column(String(30))
    site_id               = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    investigator_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_protocol_deviation = Column(Boolean, default=False)
    deviation_type        = Column(String(50))
    deviation_notes       = Column(Text)
    assessments           = Column(JSONB, default=dict)
    notes                 = Column(Text)

    patient = relationship("Patient", back_populates="visits")
    aes     = relationship("AdverseEvent", back_populates="visit")


# ─── SAE / 不良事件 ────────────────────────────────────────────────

class AdverseEvent(Base, TimestampMixin):
    __tablename__ = "adverse_events"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ae_no           = Column(String(50), unique=True, nullable=False, index=True)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    visit_id        = Column(UUID(as_uuid=True), ForeignKey("patient_visits.id"))
    description     = Column(Text, nullable=False)
    meddra_pt       = Column(String(200))
    meddra_soc      = Column(String(200))
    icd_code        = Column(String(20))
    severity        = Column(String(20))
    is_serious      = Column(Boolean, default=False, index=True)
    sae_criteria    = Column(JSONB, default=list)
    relatedness     = Column(String(30))
    onset_date      = Column(Date)
    resolution_date = Column(Date)
    outcome         = Column(String(30))
    action_taken    = Column(String(50))
    treatment       = Column(Text)
    report_status   = Column(String(20), default="INITIAL")
    reported_to_sponsor = Column(Boolean, default=False)
    sponsor_report_date = Column(Date)
    reported_to_ethics  = Column(Boolean, default=False)
    ethics_report_date  = Column(Date)
    expedited_report    = Column(Boolean, default=False)
    reported_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    patient = relationship("Patient", back_populates="aes")
    visit   = relationship("PatientVisit", back_populates="aes")


# ─── 药品管理 ──────────────────────────────────────────────────────

class DrugBatch(Base, TimestampMixin):
    __tablename__ = "drug_batches"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    batch_no        = Column(String(100), unique=True, nullable=False, index=True)
    drug_name       = Column(String(200), nullable=False)
    drug_code       = Column(String(100))
    drug_form       = Column(String(50))
    dosage          = Column(String(100))
    manufacturer    = Column(String(200))
    manufacture_date = Column(Date)
    expiry_date     = Column(Date, index=True)
    received_qty    = Column(Integer, nullable=False)
    current_qty     = Column(Integer, nullable=False)
    dispensed_qty   = Column(Integer, default=0)
    returned_qty    = Column(Integer, default=0)
    destroyed_qty   = Column(Integer, default=0)
    unit            = Column(String(20), default="片/粒")
    storage_condition = Column(String(100))
    storage_site    = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    current_temp    = Column(Numeric(5, 2))
    temp_log        = Column(JSONB, default=list)
    is_blinded      = Column(Boolean, default=False)
    unblinding_log  = Column(JSONB, default=list)
    status          = Column(String(20), default="ACTIVE")
    received_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    received_at     = Column(DateTime(timezone=True), server_default=func.now())

    dispensing_records = relationship("DrugDispensing", back_populates="batch")


class DrugDispensing(Base):
    __tablename__ = "drug_dispensing"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id        = Column(UUID(as_uuid=True), ForeignKey("drug_batches.id"))
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    visit_id        = Column(UUID(as_uuid=True), ForeignKey("patient_visits.id"))
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    dispense_qty    = Column(Integer, nullable=False)
    returned_qty    = Column(Integer, default=0)
    randomization_no = Column(String(50))
    kit_no          = Column(String(100))
    dispensed_by    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    dispensed_at    = Column(DateTime(timezone=True), server_default=func.now())
    return_at       = Column(DateTime(timezone=True))
    notes           = Column(Text)

    batch = relationship("DrugBatch", back_populates="dispensing_records")


# ─── 经费管理 ──────────────────────────────────────────────────────

class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_no     = Column(String(100), unique=True, nullable=False)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    title           = Column(String(200), nullable=False)
    contract_type   = Column(String(50))
    party_name      = Column(String(200))
    total_amount    = Column(Numeric(15, 2))
    currency        = Column(String(10), default="CNY")
    sign_date       = Column(Date)
    start_date      = Column(Date)
    end_date        = Column(Date)
    status          = Column(String(20), default="DRAFT")
    payment_terms   = Column(Text)
    doc_id          = Column(UUID(as_uuid=True))
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    payments = relationship("Payment", back_populates="contract")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id     = Column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    payment_type    = Column(String(50))
    description     = Column(Text)
    planned_amount  = Column(Numeric(15, 2))
    actual_amount   = Column(Numeric(15, 2))
    planned_date    = Column(Date)
    actual_date     = Column(Date)
    status          = Column(String(20), default="PENDING")
    invoice_no      = Column(String(100))
    invoice_date    = Column(Date)
    invoice_amount  = Column(Numeric(15, 2))
    notes           = Column(Text)
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    contract = relationship("Contract", back_populates="payments")


# ─── 质控与稽查 ────────────────────────────────────────────────────

class MonitoringReport(Base, TimestampMixin):
    __tablename__ = "monitoring_reports"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_no       = Column(String(50), unique=True, nullable=False)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    monitor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    visit_type      = Column(String(30))
    visit_date      = Column(Date)
    report_date     = Column(Date)
    overall_rating  = Column(String(20))
    findings        = Column(JSONB, default=list)
    actions         = Column(JSONB, default=list)
    status          = Column(String(20), default="DRAFT")
    approved_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at     = Column(DateTime(timezone=True))
    doc_id          = Column(UUID(as_uuid=True))


class QCIssue(Base, TimestampMixin):
    __tablename__ = "qc_issues"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_no        = Column(String(50), unique=True, nullable=False)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    report_id       = Column(UUID(as_uuid=True), ForeignKey("monitoring_reports.id"))
    category        = Column(String(50))
    severity        = Column(String(20))
    description     = Column(Text, nullable=False)
    due_date        = Column(Date)
    status          = Column(String(20), default="OPEN")
    assigned_to     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution      = Column(Text)
    resolved_at     = Column(DateTime(timezone=True))


# ─── 文档管理 ──────────────────────────────────────────────────────

class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    folder_id       = Column(UUID(as_uuid=True), ForeignKey("etmf_folders.id"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    title           = Column(String(300), nullable=False)
    doc_type        = Column(String(100))
    file_name       = Column(String(300))
    file_path       = Column(String(500))
    file_size       = Column(BigInteger)
    mime_type       = Column(String(100))
    checksum        = Column(String(64))
    version         = Column(String(20), default="1.0")
    version_notes   = Column(Text)
    previous_id     = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    is_current      = Column(Boolean, default=True)
    effective_date  = Column(Date)
    expiry_date     = Column(Date)
    requires_esig   = Column(Boolean, default=False)
    esig_status     = Column(String(20), default="NONE")
    esig_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    esig_at         = Column(DateTime(timezone=True))
    esig_cert       = Column(Text)
    status          = Column(String(20), default="DRAFT")
    reviewed_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at     = Column(DateTime(timezone=True))
    uploaded_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class ETMFFolder(Base):
    __tablename__ = "etmf_folders"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id    = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    parent_id   = Column(UUID(as_uuid=True), ForeignKey("etmf_folders.id"))
    code        = Column(String(50), nullable=False)
    name        = Column(String(200), nullable=False)
    section     = Column(String(10))
    is_required = Column(Boolean, default=True)
    sort_order  = Column(Integer, default=0)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


# ─── 患者筛选记录 ──────────────────────────────────────────────────

class ScreeningRecord(Base):
    __tablename__ = "screening_records"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    criteria_result = Column(JSONB, default=dict)   # 入排标准评估结果
    match_score     = Column(Numeric(5, 2))          # 匹配度评分 0-100
    screen_result   = Column(String(20))             # PASS / FAIL / PENDING
    fail_reason     = Column(Text)
    screened_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    screened_at     = Column(DateTime(timezone=True), server_default=func.now())


# ─── 系统配置 ──────────────────────────────────────────────────────

class SystemConfig(Base):
    __tablename__ = "system_config"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category    = Column(String(50), nullable=False)
    key         = Column(String(100), nullable=False)
    value       = Column(Text)
    description = Column(Text)
    is_editable = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── 稽查日志 ──────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id      = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    username      = Column(String(100))
    user_role     = Column(String(50))
    request_id    = Column(String(50))
    ip_address    = Column(INET)
    user_agent    = Column(String(500))
    action        = Column(String(100), nullable=False)
    module        = Column(String(50))
    resource_type = Column(String(100))
    resource_id   = Column(String(100))
    resource_name = Column(String(300))
    old_values    = Column(JSONB)
    new_values    = Column(JSONB)
    success       = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# ─── 通知 ──────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    trial_id   = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    type       = Column(String(50))
    priority   = Column(String(20), default="NORMAL")
    title      = Column(String(300), nullable=False)
    content    = Column(Text)
    data       = Column(JSONB, default=dict)
    is_read    = Column(Boolean, default=False, index=True)
    read_at    = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ═══════════════════════════════════════════════════════════════════════════
# IWRS 受试者随机化系统
# ═══════════════════════════════════════════════════════════════════════════

class RandomizationScheme(Base, TimestampMixin):
    """随机化方案"""
    __tablename__ = "randomization_schemes"
    
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_code     = Column(String(50), unique=True, nullable=False, index=True)
    scheme_name     = Column(String(200), nullable=False)
    scheme_type     = Column(String(30), nullable=False)  # RANDOM/BLOCK/STRATIFIED
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"), index=True)
    
    # 随机化参数
    block_sizes     = Column(ARRAY(Integer), default=[4])
    ratio           = Column(String(20), default="1:1")
    strata_factors  = Column(ARRAY(String), default=[])
    arms            = Column(JSONB, default=[{"code": "A", "name": "试验组"}, {"code": "B", "name": "对照组"}])
    total_subjects  = Column(Integer, nullable=False)
    
    # 盲态管理
    is_blinded      = Column(Boolean, default=True)
    blinding_method = Column(String(20), default="DOUBLE")  # SINGLE/DOUBLE/OPEN
    
    # 状态
    status          = Column(String(20), default="DRAFT")  # DRAFT/ACTIVE/PAUSED/COMPLETED/ARCHIVED
    
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    activated_at    = Column(DateTime(timezone=True))
    completed_at    = Column(DateTime(timezone=True))
    
    # 关系
    randomizations  = relationship("SubjectRandomization", back_populates="scheme")
    code_pool       = relationship("RandomizationCode", back_populates="scheme")


class SubjectRandomization(Base, TimestampMixin):
    """受试者随机化记录"""
    __tablename__ = "subject_randomizations"
    
    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id           = Column(UUID(as_uuid=True), ForeignKey("randomization_schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id          = Column(UUID(as_uuid=True), nullable=False, index=True)
    subject_code        = Column(String(50), unique=True, nullable=False)  # P-001
    
    # 随机号信息
    randomization_code  = Column(String(50), unique=True, nullable=False)  # R2026001001
    block_id            = Column(String(50))
    block_sequence      = Column(Integer)
    treatment_arm       = Column(String(50), nullable=False)  # A/B
    treatment_name      = Column(String(100))
    
    # 分层信息
    strata_values      = Column(JSONB, default={})
    
    # 盲态
    is_blinded         = Column(Boolean, default=True)
    unblinded_at       = Column(DateTime(timezone=True))
    unblinded_by       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    unblind_reason     = Column(Text)
    
    # 状态
    status              = Column(String(20), default="ASSIGNED")  # ASSIGNED/UNBLINDED/WITHDRAWN
    
    # 药品编码
    drug_code           = Column(String(50))
    kit_number          = Column(String(50))
    
    assigned_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # 关系
    scheme              = relationship("RandomizationScheme", back_populates="randomizations")


class RandomizationCode(Base):
    """随机编码表（预生成的随机号池）"""
    __tablename__ = "randomization_codes"
    
    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id           = Column(UUID(as_uuid=True), ForeignKey("randomization_schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    block_id            = Column(String(50), nullable=False)
    sequence            = Column(Integer, nullable=False)
    randomization_code  = Column(String(50), unique=True, nullable=False)
    treatment_arm       = Column(String(50), nullable=False)
    treatment_name      = Column(String(100))
    strata_values       = Column(JSONB, default={})
    is_used             = Column(Boolean, default=False, index=True)
    used_at             = Column(DateTime(timezone=True))
    used_by_subject     = Column(String(50))
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    scheme              = relationship("RandomizationScheme", back_populates="code_pool")
=======
"""
SQLAlchemy ORM 模型定义
所有数据表对应的 Python 类
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Date,
    DateTime, Numeric, BigInteger, ForeignKey, JSON,
    LargeBinary, ARRAY
)
from sqlalchemy.dialects.postgresql import INET, UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class TimestampMixin:
    """时间戳公共字段"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── 角色与用户 ────────────────────────────────────────────────────

class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code        = Column(String(50), unique=True, nullable=False, index=True)
    name        = Column(String(100), nullable=False)
    description = Column(Text)
    permissions = Column(JSONB, default=list)
    is_system   = Column(Boolean, default=False)

    users = relationship("User", back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id     = Column(String(50), unique=True)
    username        = Column(String(100), unique=True, nullable=False, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(200), nullable=False)
    phone           = Column(String(20))
    department      = Column(String(100))
    title           = Column(String(100))
    role_id         = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    is_active       = Column(Boolean, default=True)
    is_superuser    = Column(Boolean, default=False)
    last_login_at   = Column(DateTime(timezone=True))
    last_login_ip   = Column(INET)
    failed_attempts = Column(Integer, default=0)
    locked_until    = Column(DateTime(timezone=True))
    mfa_enabled     = Column(Boolean, default=False)
    mfa_secret      = Column(String(100))
    data_consent    = Column(Boolean, default=False)
    consent_at      = Column(DateTime(timezone=True))

    role = relationship("Role", back_populates="users")
    organization = relationship("Organization", back_populates="users")


class Timesheet(Base, TimestampMixin):
    __tablename__ = "timesheets"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date        = Column(Date, nullable=False)
    project     = Column(String(200), nullable=False)
    task        = Column(String(200), nullable=False)
    hours       = Column(Numeric(5, 2), nullable=False)
    notes       = Column(Text)

    user = relationship("User")


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti        = Column(String(255), unique=True, nullable=False, index=True)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    expired_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── 机构与中心 ────────────────────────────────────────────────────

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code          = Column(String(50), unique=True, nullable=False)
    name          = Column(String(200), nullable=False)
    type          = Column(String(50))
    address       = Column(Text)
    city          = Column(String(100))
    country       = Column(String(100), default="中国")
    phone         = Column(String(50))
    email         = Column(String(255))
    license_no    = Column(String(100))
    gcp_certified = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)

    users = relationship("User", back_populates="organization")
    sites = relationship("Site", back_populates="organization")


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code            = Column(String(50), unique=True, nullable=False)
    name            = Column(String(200), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    address         = Column(Text)
    pi_name         = Column(String(100))
    pi_user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    contact_phone   = Column(String(50))
    contact_email   = Column(String(255))
    status          = Column(String(20), default="ACTIVE")
    gcp_cert_expiry = Column(Date)

    organization = relationship("Organization", back_populates="sites")


# ─── 临床试验 ──────────────────────────────────────────────────────

class Trial(Base, TimestampMixin):
    __tablename__ = "trials"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_no        = Column(String(50), unique=True, nullable=False, index=True)
    short_name      = Column(String(100), nullable=False)
    full_name       = Column(Text, nullable=False)
    phase           = Column(String(10))
    status          = Column(String(30), default="PLANNING", index=True)
    type            = Column(String(50))
    indication      = Column(Text)
    drug_name       = Column(String(200))
    drug_code       = Column(String(100))
    sponsor         = Column(String(200))
    sponsor_contact = Column(String(100))
    cro             = Column(String(200))
    planned_start   = Column(Date)
    actual_start    = Column(Date)
    planned_end     = Column(Date)
    actual_end      = Column(Date)
    target_enrollment   = Column(Integer, default=0)
    enrolled_count      = Column(Integer, default=0)
    screened_count      = Column(Integer, default=0)
    screen_fail_count   = Column(Integer, default=0)
    completed_count     = Column(Integer, default=0)
    dropped_count       = Column(Integer, default=0)
    total_budget        = Column(Numeric(15, 2))
    spent_amount        = Column(Numeric(15, 2), default=0)
    currency            = Column(String(10), default="CNY")
    protocol_version    = Column(String(20))
    protocol_date       = Column(Date)
    protocol_doc_id     = Column(UUID(as_uuid=True))
    ctgov_id            = Column(String(50))
    cde_id              = Column(String(50))
    ethics_approval_no  = Column(String(100))
    pm_user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by          = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    patients    = relationship("Patient", back_populates="trial")
    milestones  = relationship("TrialMilestone", back_populates="trial")
    trial_sites = relationship("TrialSite", back_populates="trial")


class TrialSite(Base, TimestampMixin):
    __tablename__ = "trial_sites"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    status          = Column(String(20), default="INITIATING")
    target_enrollment = Column(Integer, default=0)
    enrolled_count    = Column(Integer, default=0)
    initiation_date   = Column(Date)
    close_date        = Column(Date)
    budget_allocated  = Column(Numeric(15, 2))
    budget_spent      = Column(Numeric(15, 2), default=0)
    pi_user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    trial = relationship("Trial", back_populates="trial_sites")


class TrialMilestone(Base, TimestampMixin):
    __tablename__ = "trial_milestones"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"))
    name            = Column(String(200), nullable=False)
    milestone_type  = Column(String(50))
    planned_date    = Column(Date)
    actual_date     = Column(Date)
    status          = Column(String(20), default="PENDING")
    owner_user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes           = Column(Text)

    trial = relationship("Trial", back_populates="milestones")


# ─── 患者管理 ──────────────────────────────────────────────────────

class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_no      = Column(String(50), unique=True, nullable=False, index=True)
    screening_no    = Column(String(50), index=True)
    full_name_enc   = Column(LargeBinary)       # 加密存储
    id_card_enc     = Column(LargeBinary)
    phone_enc       = Column(LargeBinary)
    email_enc       = Column(LargeBinary)
    gender          = Column(String(10))
    birth_year      = Column(Integer)
    age             = Column(Integer)
    blood_type      = Column(String(5))
    ethnicity       = Column(String(50))
    diagnosis       = Column(Text)
    icd_code        = Column(String(20))
    disease_stage   = Column(String(50))
    comorbidities   = Column(JSONB, default=list)
    status          = Column(String(30), default="SCREENING", index=True)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"), index=True)
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    assigned_to     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    consent_given   = Column(Boolean, default=False)
    consent_date    = Column(DateTime(timezone=True))
    consent_doc_id  = Column(UUID(as_uuid=True))
    gdpr_log        = Column(JSONB, default=list)
    emr_patient_id  = Column(String(100))
    hl7_fhir_id     = Column(String(100))
    screening_date  = Column(Date)
    enrollment_date = Column(Date)
    completion_date = Column(Date)
    arm             = Column(String(50))
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    trial   = relationship("Trial", back_populates="patients")
    visits  = relationship("PatientVisit", back_populates="patient")
    aes     = relationship("AdverseEvent", back_populates="patient")
    econsents = relationship("EConsent", back_populates="patient")


class EConsent(Base, TimestampMixin):
    __tablename__ = "econsents"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"))
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    version         = Column(String(20), nullable=False)
    language        = Column(String(20), default="zh-CN")
    template_id     = Column(UUID(as_uuid=True))
    status          = Column(String(20), default="PENDING")
    patient_signature       = Column(Text)
    patient_signed_at       = Column(DateTime(timezone=True))
    patient_ip              = Column(String(45))
    patient_cert_fingerprint = Column(String(255))
    witness_user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    witness_signature       = Column(Text)
    witness_signed_at       = Column(DateTime(timezone=True))
    lar_name                = Column(String(100))
    lar_relationship        = Column(String(50))
    lar_signature           = Column(Text)
    lar_signed_at           = Column(DateTime(timezone=True))
    gdpr_basis              = Column(String(50), default="CONSENT")
    data_purposes           = Column(JSONB, default=list)
    withdrawal_at           = Column(DateTime(timezone=True))
    doc_id                  = Column(UUID(as_uuid=True))

    patient = relationship("Patient", back_populates="econsents")


# ─── 访视管理 ──────────────────────────────────────────────────────

class VisitSchedule(Base):
    __tablename__ = "visit_schedules"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id", ondelete="CASCADE"))
    visit_name      = Column(String(100), nullable=False)
    visit_type      = Column(String(30))
    visit_order     = Column(Integer)
    window_target   = Column(Integer)
    window_minus    = Column(Integer, default=3)
    window_plus     = Column(Integer, default=3)
    is_mandatory    = Column(Boolean, default=True)
    assessment_list = Column(JSONB, default=list)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class PatientVisit(Base, TimestampMixin):
    __tablename__ = "patient_visits"

    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id            = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    trial_id              = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    schedule_id           = Column(UUID(as_uuid=True), ForeignKey("visit_schedules.id"))
    visit_name            = Column(String(100))
    planned_date          = Column(Date)
    actual_date           = Column(Date)
    status                = Column(String(20), default="SCHEDULED")
    visit_type            = Column(String(30))
    site_id               = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    investigator_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_protocol_deviation = Column(Boolean, default=False)
    deviation_type        = Column(String(50))
    deviation_notes       = Column(Text)
    assessments           = Column(JSONB, default=dict)
    notes                 = Column(Text)

    patient = relationship("Patient", back_populates="visits")
    aes     = relationship("AdverseEvent", back_populates="visit")


# ─── SAE / 不良事件 ────────────────────────────────────────────────

class AdverseEvent(Base, TimestampMixin):
    __tablename__ = "adverse_events"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ae_no           = Column(String(50), unique=True, nullable=False, index=True)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    visit_id        = Column(UUID(as_uuid=True), ForeignKey("patient_visits.id"))
    description     = Column(Text, nullable=False)
    meddra_pt       = Column(String(200))
    meddra_soc      = Column(String(200))
    icd_code        = Column(String(20))
    severity        = Column(String(20))
    is_serious      = Column(Boolean, default=False, index=True)
    sae_criteria    = Column(JSONB, default=list)
    relatedness     = Column(String(30))
    onset_date      = Column(Date)
    resolution_date = Column(Date)
    outcome         = Column(String(30))
    action_taken    = Column(String(50))
    treatment       = Column(Text)
    report_status   = Column(String(20), default="INITIAL")
    reported_to_sponsor = Column(Boolean, default=False)
    sponsor_report_date = Column(Date)
    reported_to_ethics  = Column(Boolean, default=False)
    ethics_report_date  = Column(Date)
    expedited_report    = Column(Boolean, default=False)
    reported_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    patient = relationship("Patient", back_populates="aes")
    visit   = relationship("PatientVisit", back_populates="aes")


# ─── 药品管理 ──────────────────────────────────────────────────────

class DrugBatch(Base, TimestampMixin):
    __tablename__ = "drug_batches"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    batch_no        = Column(String(100), unique=True, nullable=False, index=True)
    drug_name       = Column(String(200), nullable=False)
    drug_code       = Column(String(100))
    drug_form       = Column(String(50))
    dosage          = Column(String(100))
    manufacturer    = Column(String(200))
    manufacture_date = Column(Date)
    expiry_date     = Column(Date, index=True)
    received_qty    = Column(Integer, nullable=False)
    current_qty     = Column(Integer, nullable=False)
    dispensed_qty   = Column(Integer, default=0)
    returned_qty    = Column(Integer, default=0)
    destroyed_qty   = Column(Integer, default=0)
    unit            = Column(String(20), default="片/粒")
    storage_condition = Column(String(100))
    storage_site    = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    current_temp    = Column(Numeric(5, 2))
    temp_log        = Column(JSONB, default=list)
    is_blinded      = Column(Boolean, default=False)
    unblinding_log  = Column(JSONB, default=list)
    status          = Column(String(20), default="ACTIVE")
    received_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    received_at     = Column(DateTime(timezone=True), server_default=func.now())

    dispensing_records = relationship("DrugDispensing", back_populates="batch")


class DrugDispensing(Base):
    __tablename__ = "drug_dispensing"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id        = Column(UUID(as_uuid=True), ForeignKey("drug_batches.id"))
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    visit_id        = Column(UUID(as_uuid=True), ForeignKey("patient_visits.id"))
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    dispense_qty    = Column(Integer, nullable=False)
    returned_qty    = Column(Integer, default=0)
    randomization_no = Column(String(50))
    kit_no          = Column(String(100))
    dispensed_by    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    dispensed_at    = Column(DateTime(timezone=True), server_default=func.now())
    return_at       = Column(DateTime(timezone=True))
    notes           = Column(Text)

    batch = relationship("DrugBatch", back_populates="dispensing_records")


# ─── 经费管理 ──────────────────────────────────────────────────────

class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_no     = Column(String(100), unique=True, nullable=False)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    title           = Column(String(200), nullable=False)
    contract_type   = Column(String(50))
    party_name      = Column(String(200))
    total_amount    = Column(Numeric(15, 2))
    currency        = Column(String(10), default="CNY")
    sign_date       = Column(Date)
    start_date      = Column(Date)
    end_date        = Column(Date)
    status          = Column(String(20), default="DRAFT")
    payment_terms   = Column(Text)
    doc_id          = Column(UUID(as_uuid=True))
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    payments = relationship("Payment", back_populates="contract")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id     = Column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    payment_type    = Column(String(50))
    description     = Column(Text)
    planned_amount  = Column(Numeric(15, 2))
    actual_amount   = Column(Numeric(15, 2))
    planned_date    = Column(Date)
    actual_date     = Column(Date)
    status          = Column(String(20), default="PENDING")
    invoice_no      = Column(String(100))
    invoice_date    = Column(Date)
    invoice_amount  = Column(Numeric(15, 2))
    notes           = Column(Text)
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    contract = relationship("Contract", back_populates="payments")


# ─── 质控与稽查 ────────────────────────────────────────────────────

class MonitoringReport(Base, TimestampMixin):
    __tablename__ = "monitoring_reports"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_no       = Column(String(50), unique=True, nullable=False)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    monitor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    visit_type      = Column(String(30))
    visit_date      = Column(Date)
    report_date     = Column(Date)
    overall_rating  = Column(String(20))
    findings        = Column(JSONB, default=list)
    actions         = Column(JSONB, default=list)
    status          = Column(String(20), default="DRAFT")
    approved_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at     = Column(DateTime(timezone=True))
    doc_id          = Column(UUID(as_uuid=True))


class QCIssue(Base, TimestampMixin):
    __tablename__ = "qc_issues"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_no        = Column(String(50), unique=True, nullable=False)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    report_id       = Column(UUID(as_uuid=True), ForeignKey("monitoring_reports.id"))
    category        = Column(String(50))
    severity        = Column(String(20))
    description     = Column(Text, nullable=False)
    due_date        = Column(Date)
    status          = Column(String(20), default="OPEN")
    assigned_to     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution      = Column(Text)
    resolved_at     = Column(DateTime(timezone=True))


# ─── 文档管理 ──────────────────────────────────────────────────────

class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    folder_id       = Column(UUID(as_uuid=True), ForeignKey("etmf_folders.id"))
    site_id         = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    title           = Column(String(300), nullable=False)
    doc_type        = Column(String(100))
    file_name       = Column(String(300))
    file_path       = Column(String(500))
    file_size       = Column(BigInteger)
    mime_type       = Column(String(100))
    checksum        = Column(String(64))
    version         = Column(String(20), default="1.0")
    version_notes   = Column(Text)
    previous_id     = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    is_current      = Column(Boolean, default=True)
    effective_date  = Column(Date)
    expiry_date     = Column(Date)
    requires_esig   = Column(Boolean, default=False)
    esig_status     = Column(String(20), default="NONE")
    esig_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    esig_at         = Column(DateTime(timezone=True))
    esig_cert       = Column(Text)
    status          = Column(String(20), default="DRAFT")
    reviewed_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at     = Column(DateTime(timezone=True))
    uploaded_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))


class ETMFFolder(Base):
    __tablename__ = "etmf_folders"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trial_id    = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    parent_id   = Column(UUID(as_uuid=True), ForeignKey("etmf_folders.id"))
    code        = Column(String(50), nullable=False)
    name        = Column(String(200), nullable=False)
    section     = Column(String(10))
    is_required = Column(Boolean, default=True)
    sort_order  = Column(Integer, default=0)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


# ─── 患者筛选记录 ──────────────────────────────────────────────────

class ScreeningRecord(Base):
    __tablename__ = "screening_records"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id      = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    criteria_result = Column(JSONB, default=dict)   # 入排标准评估结果
    match_score     = Column(Numeric(5, 2))          # 匹配度评分 0-100
    screen_result   = Column(String(20))             # PASS / FAIL / PENDING
    fail_reason     = Column(Text)
    screened_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    screened_at     = Column(DateTime(timezone=True), server_default=func.now())


# ─── 系统配置 ──────────────────────────────────────────────────────

class SystemConfig(Base):
    __tablename__ = "system_config"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category    = Column(String(50), nullable=False)
    key         = Column(String(100), nullable=False)
    value       = Column(Text)
    description = Column(Text)
    is_editable = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── 稽查日志 ──────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id      = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    username      = Column(String(100))
    user_role     = Column(String(50))
    request_id    = Column(String(50))
    ip_address    = Column(INET)
    user_agent    = Column(String(500))
    action        = Column(String(100), nullable=False)
    module        = Column(String(50))
    resource_type = Column(String(100))
    resource_id   = Column(String(100))
    resource_name = Column(String(300))
    old_values    = Column(JSONB)
    new_values    = Column(JSONB)
    success       = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# ─── 通知 ──────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    trial_id   = Column(UUID(as_uuid=True), ForeignKey("trials.id"))
    type       = Column(String(50))
    priority   = Column(String(20), default="NORMAL")
    title      = Column(String(300), nullable=False)
    content    = Column(Text)
    data       = Column(JSONB, default=dict)
    is_read    = Column(Boolean, default=False, index=True)
    read_at    = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ═══════════════════════════════════════════════════════════════════════════
# IWRS 受试者随机化系统
# ═══════════════════════════════════════════════════════════════════════════

class RandomizationScheme(Base, TimestampMixin):
    """随机化方案"""
    __tablename__ = "randomization_schemes"
    
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_code     = Column(String(50), unique=True, nullable=False, index=True)
    scheme_name     = Column(String(200), nullable=False)
    scheme_type     = Column(String(30), nullable=False)  # RANDOM/BLOCK/STRATIFIED
    trial_id        = Column(UUID(as_uuid=True), ForeignKey("trials.id"), index=True)
    
    # 随机化参数
    block_sizes     = Column(ARRAY(Integer), default=[4])
    ratio           = Column(String(20), default="1:1")
    strata_factors  = Column(ARRAY(String), default=[])
    arms            = Column(JSONB, default=[{"code": "A", "name": "试验组"}, {"code": "B", "name": "对照组"}])
    total_subjects  = Column(Integer, nullable=False)
    
    # 盲态管理
    is_blinded      = Column(Boolean, default=True)
    blinding_method = Column(String(20), default="DOUBLE")  # SINGLE/DOUBLE/OPEN
    
    # 状态
    status          = Column(String(20), default="DRAFT")  # DRAFT/ACTIVE/PAUSED/COMPLETED/ARCHIVED
    
    created_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    activated_at    = Column(DateTime(timezone=True))
    completed_at    = Column(DateTime(timezone=True))
    
    # 关系
    randomizations  = relationship("SubjectRandomization", back_populates="scheme")
    code_pool       = relationship("RandomizationCode", back_populates="scheme")


class SubjectRandomization(Base, TimestampMixin):
    """受试者随机化记录"""
    __tablename__ = "subject_randomizations"
    
    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id           = Column(UUID(as_uuid=True), ForeignKey("randomization_schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id          = Column(UUID(as_uuid=True), nullable=False, index=True)
    subject_code        = Column(String(50), unique=True, nullable=False)  # P-001
    
    # 随机号信息
    randomization_code  = Column(String(50), unique=True, nullable=False)  # R2026001001
    block_id            = Column(String(50))
    block_sequence      = Column(Integer)
    treatment_arm       = Column(String(50), nullable=False)  # A/B
    treatment_name      = Column(String(100))
    
    # 分层信息
    strata_values      = Column(JSONB, default={})
    
    # 盲态
    is_blinded         = Column(Boolean, default=True)
    unblinded_at       = Column(DateTime(timezone=True))
    unblinded_by       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    unblind_reason     = Column(Text)
    
    # 状态
    status              = Column(String(20), default="ASSIGNED")  # ASSIGNED/UNBLINDED/WITHDRAWN
    
    # 药品编码
    drug_code           = Column(String(50))
    kit_number          = Column(String(50))
    
    assigned_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # 关系
    scheme              = relationship("RandomizationScheme", back_populates="randomizations")


class RandomizationCode(Base):
    """随机编码表（预生成的随机号池）"""
    __tablename__ = "randomization_codes"
    
    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id           = Column(UUID(as_uuid=True), ForeignKey("randomization_schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    block_id            = Column(String(50), nullable=False)
    sequence            = Column(Integer, nullable=False)
    randomization_code  = Column(String(50), unique=True, nullable=False)
    treatment_arm       = Column(String(50), nullable=False)
    treatment_name      = Column(String(100))
    strata_values       = Column(JSONB, default={})
    is_used             = Column(Boolean, default=False, index=True)
    used_at             = Column(DateTime(timezone=True))
    used_by_subject     = Column(String(50))
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    scheme              = relationship("RandomizationScheme", back_populates="code_pool")
>>>>>>> origin/main
