from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.prediction import PredictionHistory
from app.models.product import Product
from app.models.user import User
from app.schemas.forecast import ActualQuantityUpdate, PredictionRead

router = APIRouter(prefix="/predictions", tags=["Prediction History"])


@router.get("", response_model=List[PredictionRead])
def list_predictions(
    product_id: Optional[int] = Query(None, gt=0),
    user_id: Optional[int] = Query(None, gt=0),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    model_version: Optional[str] = Query(None, max_length=64),
    search: Optional[str] = Query(None, min_length=1, max_length=150),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before end_date")
    if role != "admin" and user_id is not None and user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only view your own prediction history")

    query = db.query(PredictionHistory).outerjoin(Product, PredictionHistory.product_id == Product.product_id)
    if role != "admin":
        query = query.filter(PredictionHistory.user_id == current_user.user_id)
    elif user_id is not None:
        query = query.filter(PredictionHistory.user_id == user_id)
    if product_id is not None:
        query = query.filter(PredictionHistory.product_id == product_id)
    if start_date:
        query = query.filter(PredictionHistory.forecast_date >= start_date)
    if end_date:
        query = query.filter(PredictionHistory.forecast_date <= end_date)
    if model_version:
        query = query.filter(PredictionHistory.model_version == model_version)
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Product.product_name.ilike(search_term),
            Product.category.ilike(search_term),
            PredictionHistory.model_name.ilike(search_term),
            PredictionHistory.model_version.ilike(search_term),
            cast(PredictionHistory.prediction_id, String).ilike(search_term),
        ))
    return query.order_by(PredictionHistory.predicted_at.desc()).offset(offset).limit(limit).all()


@router.patch("/{prediction_id}/actual", response_model=PredictionRead)
def record_actual_quantity(
    prediction_id: int,
    payload: ActualQuantityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
):
    prediction = db.query(PredictionHistory).filter(PredictionHistory.prediction_id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    prediction.actual_quantity = payload.actual_quantity
    db.commit()
    db.refresh(prediction)
    return prediction