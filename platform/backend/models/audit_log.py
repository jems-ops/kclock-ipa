from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base


class AuditLog(Base):
    """Immutable record of every platform action for compliance evidence."""
    __tablename__ = "audit_logs"

    id         = Column(String, primary_key=True)
    app_id     = Column(String, ForeignKey("apps.id"), nullable=True)  # None = platform-level
    actor      = Column(String, nullable=False)          # user or "system"
    action     = Column(String, nullable=False)          # e.g. "onboard", "diagnose", "compliance_scan"
    resource   = Column(String)                          # e.g. "jenkins", "wazuh"
    detail     = Column(Text)                            # JSON payload / free text
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    app = relationship("App", back_populates="audit_logs")
