from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.base import get_db
from schemas import DiagnoseJobCreate, DiagnoseJobOut
import services
import os

router = APIRouter(prefix="/diagnose", tags=["diagnose"])

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:270m")

@router.get("", response_model=list[DiagnoseJobOut])
def list_jobs(app_id: str | None = None, db: Session = Depends(get_db)):
    return services.get_diagnose_jobs(db, app_id)

@router.post("", response_model=DiagnoseJobOut, status_code=201)
def diagnose(data: DiagnoseJobCreate, db: Session = Depends(get_db)):
    if not services.get_app(db, data.app_id):
        raise HTTPException(404, "App not found")
    try:
        from sso_cli.ai.troubleshoot_agent import diagnose as ai_diagnose
        result = ai_diagnose(data.app_id, data.question)
    except Exception as e:
        result = f"AI unavailable: {e}"
    return services.create_diagnose_job(db, data, diagnosis=result, model_used=OLLAMA_MODEL)
