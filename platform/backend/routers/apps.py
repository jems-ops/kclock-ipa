from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.base import get_db
from schemas import AppCreate, AppUpdate, AppOut
import services

router = APIRouter(prefix="/apps", tags=["apps"])

@router.get("", response_model=list[AppOut])
def list_apps(db: Session = Depends(get_db)):
    return services.get_apps(db)

@router.get("/{app_id}", response_model=AppOut)
def get_app(app_id: str, db: Session = Depends(get_db)):
    app = services.get_app(db, app_id)
    if not app:
        raise HTTPException(404, "App not found")
    return app

@router.post("", response_model=AppOut, status_code=201)
def create_app(data: AppCreate, db: Session = Depends(get_db)):
    return services.create_app(db, data)

@router.patch("/{app_id}", response_model=AppOut)
def update_app(app_id: str, data: AppUpdate, db: Session = Depends(get_db)):
    app = services.update_app(db, app_id, data)
    if not app:
        raise HTTPException(404, "App not found")
    return app

@router.delete("/{app_id}", status_code=204)
def delete_app(app_id: str, db: Session = Depends(get_db)):
    if not services.delete_app(db, app_id):
        raise HTTPException(404, "App not found")
