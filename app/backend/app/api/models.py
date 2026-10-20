from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.audit_helper import log_audit_event
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.model_run import ModelRun
from app.models.user import User
from app.schemas.model import ModelRunRead, TrainingResponse
from app.services.forecasting_service import train_and_activate_model

router = APIRouter(prefix="/models", tags=["Forecast Models"])


@router.get("/active", response_model=Optional[ModelRunRead])
def get_active_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(ModelRun).filter(
        ModelRun.is_active.is_(True),
        ModelRun.training_status == "succeeded",
    ).order_by(ModelRun.trained_at.desc()).first()


@router.get("/runs", response_model=List[ModelRunRead])
def list_model_runs(
    training_status: Optional[str] = Query(None, max_length=20),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ModelRun)
    if training_status:
        query = query.filter(ModelRun.training_status == training_status)
    return query.order_by(ModelRun.trained_at.desc(), ModelRun.model_run_id.desc()).offset(offset).limit(limit).all()


@router.post("/retrain", response_model=TrainingResponse)
def manually_retrain_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    result = train_and_activate_model(db)
    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="RETRAIN_MODEL",
        module="FORECASTING",
        description=f"Manual model retraining finished with status '{result['training_status']}' (version {result['model_version']}).",
    )
    db.commit()
    return result