from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from db.base import Base


class ComplianceStatus(str, enum.Enum):
    compliant     = "compliant"
    non_compliant = "non_compliant"
    unknown       = "unknown"


class ComplianceReport(Base):
    """STIG/SRG compliance scan result for an app host."""
    __tablename__ = "compliance_reports"

    id             = Column(String, primary_key=True)
    app_id         = Column(String, ForeignKey("apps.id"), nullable=False)
    stig_profile   = Column(String, nullable=False)          # e.g. "RHEL9-STIG"
    status         = Column(Enum(ComplianceStatus), default=ComplianceStatus.unknown)
    total_controls = Column(Integer, default=0)
    passed         = Column(Integer, default=0)
    failed         = Column(Integer, default=0)
    not_applicable = Column(Integer, default=0)
    findings       = Column(Text)                            # JSON array of failed control IDs
    ai_summary     = Column(Text)                            # LLM-generated remediation summary
    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    app = relationship("App", back_populates="compliance_reports")
