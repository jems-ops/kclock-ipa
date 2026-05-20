from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.base import get_db
from schemas import ComplianceReportCreate, ComplianceReportOut
import services

router = APIRouter(prefix="/compliance", tags=["compliance"])

@router.get("", response_model=list[ComplianceReportOut])
def list_reports(app_id: str | None = None, db: Session = Depends(get_db)):
    return services.get_compliance_reports(db, app_id)

@router.post("", response_model=ComplianceReportOut, status_code=201)
def create_report(data: ComplianceReportCreate, db: Session = Depends(get_db)):
    if not services.get_app(db, data.app_id):
        raise HTTPException(404, "App not found")
    return services.create_compliance_report(db, data)
