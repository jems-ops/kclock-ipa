from sqlalchemy import Column, String, DateTime, Text, Enum
from datetime import datetime, timezone
import enum
from db.base import Base


class FedJobStatus(str, enum.Enum):
    pending   = "pending"
    running   = "running"
    succeeded = "succeeded"
    failed    = "failed"


class FedJobType(str, enum.Enum):
    full_federation  = "full_federation"   # freeipa_prep + ldap
    freeipa_prep     = "freeipa_prep"      # only FreeIPA side
    ldap_only        = "ldap_only"         # only Keycloak LDAP wiring
    user_sync        = "user_sync"         # trigger LDAP sync only


class LdapFederationJob(Base):
    __tablename__ = "ldap_federation_jobs"

    id           = Column(String, primary_key=True)
    job_type     = Column(Enum(FedJobType), default=FedJobType.full_federation, nullable=False)
    status       = Column(Enum(FedJobStatus), default=FedJobStatus.pending, nullable=False)
    triggered_by = Column(String, nullable=False, default="manual")
    log_output   = Column(Text)
    error        = Column(Text)
    started_at   = Column(DateTime)
    finished_at  = Column(DateTime)
    created_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))
