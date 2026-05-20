from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.base import get_db
from schemas import AuditLogOut
import services

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("", response_model=list[AuditLogOut])
def list_logs(app_id: str | None = None, db: Session = Depends(get_db)):
    return services.get_audit_logs(db, app_id)
