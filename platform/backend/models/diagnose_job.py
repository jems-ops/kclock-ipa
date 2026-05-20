from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base


class DiagnoseJob(Base):
    """Records an AI troubleshooting request and its result."""
    __tablename__ = "diagnose_jobs"

    id         = Column(String, primary_key=True)
    app_id     = Column(String, ForeignKey("apps.id"), nullable=False)
    question   = Column(Text, nullable=False)
    diagnosis  = Column(Text)                    # LLM response
    model_used = Column(String)                  # e.g. "gemma3:270m"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    app = relationship("App", back_populates="diagnose_jobs")
