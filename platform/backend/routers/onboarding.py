from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.base import get_db
from schemas import OnboardingJobCreate, OnboardingJobOut
import services
from services.ansible_runner import run_sso_onboarding, run_monitoring_agents

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("", response_model=list[OnboardingJobOut])
def list_jobs(app_id: str | None = None, db: Session = Depends(get_db)):
    return services.get_onboarding_jobs(db, app_id)


@router.post("", response_model=OnboardingJobOut, status_code=201)
def create_job(data: OnboardingJobCreate, db: Session = Depends(get_db)):
    if not services.get_app(db, data.app_id):
        raise HTTPException(404, "App not found")
    return services.create_onboarding_job(db, data)


# Static routes MUST be declared before parameterised /{job_id} routes
@router.post("/monitoring-agents", response_model=OnboardingJobOut, status_code=201)
def deploy_monitoring_agents(db: Session = Depends(get_db)):
    """Deploy node_exporter monitoring agents to all application servers.

    Creates a job record and launches the monitoring-agents Ansible playbook
    in the background. Poll GET /onboarding/{job_id} to track progress.
    """
    data = OnboardingJobCreate(app_id="prometheus", triggered_by="api")
    if not services.get_app(db, data.app_id):
        raise HTTPException(404, "Prometheus app not registered — run seed first")
    job = services.create_onboarding_job(db, data)
    job.playbook = "monitoring-agents.yml"
    db.commit(); db.refresh(job)

    run_monitoring_agents(job.id)
    return job


@router.get("/{job_id}", response_model=OnboardingJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(services.OnboardingJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/{job_id}/cancel", response_model=OnboardingJobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel a pending or running job."""
    from models.onboarding_job import JobStatus
    job = db.query(services.OnboardingJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status not in (JobStatus.pending, JobStatus.running):
        raise HTTPException(409, f"Cannot cancel a {job.status.value} job")
    return services.update_onboarding_job(db, job_id, JobStatus.failed, error="Cancelled by user")


@router.post("/{job_id}/execute", response_model=OnboardingJobOut)
def execute_job(job_id: str, db: Session = Depends(get_db)):
    """Trigger the SSO onboarding Ansible playbook for an existing job."""
    from models.onboarding_job import JobStatus
    from services.ansible_runner import APP_PLAYBOOK_MAP

    job = db.query(services.OnboardingJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.pending:
        raise HTTPException(409, f"Job already {job.status.value}")

    playbook = APP_PLAYBOOK_MAP.get(job.app_id)
    if not playbook:
        raise HTTPException(400, f"No playbook mapped for app '{job.app_id}'")

    job.playbook = playbook
    db.commit(); db.refresh(job)

    run_sso_onboarding(job.id, job.app_id)
    return job
