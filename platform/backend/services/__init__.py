import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import App, OnboardingJob, DiagnoseJob, ComplianceReport, AuditLog
from models.onboarding_job import JobStatus
from schemas import AppCreate, AppUpdate, OnboardingJobCreate, DiagnoseJobCreate, ComplianceReportCreate


def _now():
    return datetime.now(timezone.utc)


# ── App ───────────────────────────────────────────────────────────────────────

def get_apps(db: Session):
    return db.query(App).all()

def get_app(db: Session, app_id: str):
    return db.query(App).filter(App.id == app_id).first()

def create_app(db: Session, data: AppCreate):
    app = App(**data.model_dump())
    db.add(app); db.commit(); db.refresh(app)
    _write_audit(db, actor="system", action="app.create", resource=app.id, app_id=app.id)
    return app

def update_app(db: Session, app_id: str, data: AppUpdate):
    app = get_app(db, app_id)
    if not app:
        return None
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(app, k, v)
    app.updated_at = _now()
    db.commit(); db.refresh(app)
    return app

def delete_app(db: Session, app_id: str):
    app = get_app(db, app_id)
    if app:
        db.delete(app); db.commit()
    return app


# ── OnboardingJob ─────────────────────────────────────────────────────────────

def get_onboarding_jobs(db: Session, app_id: str | None = None):
    q = db.query(OnboardingJob)
    if app_id:
        q = q.filter(OnboardingJob.app_id == app_id)
    return q.order_by(OnboardingJob.created_at.desc()).all()

def create_onboarding_job(db: Session, data: OnboardingJobCreate):
    job = OnboardingJob(id=str(uuid.uuid4()), **data.model_dump())
    db.add(job); db.commit(); db.refresh(job)
    _write_audit(db, actor=data.triggered_by, action="onboard.start",
                 resource=data.app_id, app_id=data.app_id)
    return job

def update_onboarding_job(db: Session, job_id: str, status: JobStatus,
                           log_output: str = None, error: str = None):
    job = db.query(OnboardingJob).filter(OnboardingJob.id == job_id).first()
    if not job:
        return None
    job.status = status
    if log_output is not None:
        job.log_output = log_output
    if error is not None:
        job.error = error
    if status == JobStatus.running and not job.started_at:
        job.started_at = _now()
    if status in (JobStatus.succeeded, JobStatus.failed):
        job.finished_at = _now()
    db.commit(); db.refresh(job)
    return job


# ── DiagnoseJob ───────────────────────────────────────────────────────────────

def get_diagnose_jobs(db: Session, app_id: str | None = None):
    q = db.query(DiagnoseJob)
    if app_id:
        q = q.filter(DiagnoseJob.app_id == app_id)
    return q.order_by(DiagnoseJob.created_at.desc()).all()

def create_diagnose_job(db: Session, data: DiagnoseJobCreate,
                         diagnosis: str = None, model_used: str = None):
    job = DiagnoseJob(
        id=str(uuid.uuid4()),
        app_id=data.app_id,
        question=data.question,
        diagnosis=diagnosis,
        model_used=model_used,
    )
    db.add(job); db.commit(); db.refresh(job)
    _write_audit(db, actor="system", action="diagnose", resource=data.app_id, app_id=data.app_id)
    return job


# ── ComplianceReport ──────────────────────────────────────────────────────────

def get_compliance_reports(db: Session, app_id: str | None = None):
    q = db.query(ComplianceReport)
    if app_id:
        q = q.filter(ComplianceReport.app_id == app_id)
    return q.order_by(ComplianceReport.created_at.desc()).all()

def create_compliance_report(db: Session, data: ComplianceReportCreate):
    report = ComplianceReport(id=str(uuid.uuid4()), **data.model_dump())
    db.add(report); db.commit(); db.refresh(report)
    _write_audit(db, actor="system", action="compliance.scan",
                 resource=data.app_id, app_id=data.app_id)
    return report


# ── AuditLog ──────────────────────────────────────────────────────────────────

def get_audit_logs(db: Session, app_id: str | None = None):
    q = db.query(AuditLog)
    if app_id:
        q = q.filter(AuditLog.app_id == app_id)
    return q.order_by(AuditLog.created_at.desc()).all()

def _write_audit(db: Session, actor: str, action: str,
                  resource: str = None, app_id: str = None, detail: str = None):
    log = AuditLog(id=str(uuid.uuid4()), actor=actor, action=action,
                   resource=resource, app_id=app_id, detail=detail)
    db.add(log); db.commit()
