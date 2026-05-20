from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from models.onboarding_job import JobStatus
from models.compliance_report import ComplianceStatus


# ── App ───────────────────────────────────────────────────────────────────────

class AppCreate(BaseModel):
    id:            str
    name:          str
    base_url:      str
    host_group:    str
    service_name:  str
    saml_client_id: str
    enabled:       bool = True

class AppUpdate(BaseModel):
    name:          Optional[str] = None
    base_url:      Optional[str] = None
    host_group:    Optional[str] = None
    service_name:  Optional[str] = None
    saml_client_id: Optional[str] = None
    enabled:       Optional[bool] = None

class AppOut(AppCreate):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime
    updated_at: datetime


# ── OnboardingJob ─────────────────────────────────────────────────────────────

class OnboardingJobCreate(BaseModel):
    app_id:       str
    triggered_by: str = "manual"

class OnboardingJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:           str
    app_id:       str
    triggered_by: str
    status:       JobStatus
    playbook:     Optional[str]
    log_output:   Optional[str]
    error:        Optional[str]
    started_at:   Optional[datetime]
    finished_at:  Optional[datetime]
    created_at:   datetime


# ── DiagnoseJob ───────────────────────────────────────────────────────────────

class DiagnoseJobCreate(BaseModel):
    app_id:   str
    question: str

class DiagnoseJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         str
    app_id:     str
    question:   str
    diagnosis:  Optional[str]
    model_used: Optional[str]
    created_at: datetime


# ── ComplianceReport ──────────────────────────────────────────────────────────

class ComplianceReportCreate(BaseModel):
    app_id:        str
    stig_profile:  str

class ComplianceReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:             str
    app_id:         str
    stig_profile:   str
    status:         ComplianceStatus
    total_controls: int
    passed:         int
    failed:         int
    not_applicable: int
    findings:       Optional[str]
    ai_summary:     Optional[str]
    created_at:     datetime


# ── AuditLog ──────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         str
    app_id:     Optional[str]
    actor:      str
    action:     str
    resource:   Optional[str]
    detail:     Optional[str]
    created_at: datetime


# ── LdapFederationJob ─────────────────────────────────────────────────────────

from models.ldap_federation_job import FedJobStatus, FedJobType  # noqa: E402

class LdapFederationJobCreate(BaseModel):
    job_type:     FedJobType = FedJobType.full_federation
    triggered_by: str = "manual"

class LdapFederationJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:           str
    job_type:     FedJobType
    status:       FedJobStatus
    triggered_by: str
    log_output:   Optional[str]
    error:        Optional[str]
    started_at:   Optional[datetime]
    finished_at:  Optional[datetime]
    created_at:   datetime
