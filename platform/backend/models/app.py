from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base


class App(Base):
    """A SAML service provider managed by the platform."""
    __tablename__ = "apps"

    id           = Column(String, primary_key=True)          # e.g. "jenkins"
    name         = Column(String, nullable=False)             # display name
    base_url     = Column(String, nullable=False)             # https://jenkins.local
    host_group   = Column(String, nullable=False)             # Ansible inventory group
    service_name = Column(String, nullable=False)             # systemd service
    saml_client_id = Column(String, nullable=False)           # Keycloak client ID
    enabled      = Column(Boolean, default=True, nullable=False)
    created_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    onboarding_jobs   = relationship("OnboardingJob",   back_populates="app", cascade="all, delete-orphan")
    diagnose_jobs     = relationship("DiagnoseJob",     back_populates="app", cascade="all, delete-orphan")
    compliance_reports = relationship("ComplianceReport", back_populates="app", cascade="all, delete-orphan")
    audit_logs        = relationship("AuditLog",        back_populates="app", cascade="all, delete-orphan")
