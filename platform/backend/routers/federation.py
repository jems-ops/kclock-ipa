import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.base import get_db
from models.ldap_federation_job import LdapFederationJob, FedJobStatus, FedJobType
from schemas import LdapFederationJobCreate, LdapFederationJobOut
from services.ansible_runner import run_federation

router = APIRouter(prefix="/federation", tags=["federation"])


@router.get("", response_model=list[LdapFederationJobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(LdapFederationJob).order_by(LdapFederationJob.created_at.desc()).all()


@router.post("", response_model=LdapFederationJobOut, status_code=201)
def create_job(data: LdapFederationJobCreate, db: Session = Depends(get_db)):
    job = LdapFederationJob(
        id=str(uuid.uuid4()),
        job_type=data.job_type,
        triggered_by=data.triggered_by,
    )
    db.add(job); db.commit(); db.refresh(job)
    run_federation(job.id, job.job_type)
    return job


@router.get("/{job_id}", response_model=LdapFederationJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(LdapFederationJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/{job_id}/cancel", response_model=LdapFederationJobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(LdapFederationJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status not in (FedJobStatus.pending, FedJobStatus.running):
        raise HTTPException(409, f"Cannot cancel a {job.status.value} job")
    job.status = FedJobStatus.failed
    job.error = "Cancelled by user"
    job.finished_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(job)
    return job
