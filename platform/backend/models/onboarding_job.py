from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from db.base import Base


class JobStatus(str, enum.Enum):
    pending   = "pending"
    running   = "running"
    succeeded = "succeeded"
    failed    = "failed"


class OnboardingJob(Base):
    """Tracks an AI-assisted or manual SAML onboarding run for an app."""
    __tablename__ = "onboarding_jobs"

    id         = Column(String, primary_key=True)
    app_id     = Column(String, ForeignKey("apps.id"), nullable=False)
    triggered_by = Column(String, nullable=False, default="manual")  # "manual" | "ai"
    status     = Column(Enum(JobStatus), default=JobStatus.pending, nullable=False)
    playbook   = Column(String)                   # playbook filename executed
    log_output = Column(Text)                     # captured ansible stdout
    error      = Column(Text)
    started_at  = Column(DateTime)
    finished_at = Column(DateTime)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    app = relationship("App", back_populates="onboarding_jobs")
