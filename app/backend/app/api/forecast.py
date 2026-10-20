from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.forecast import ForecastRequest, ForecastResponse

from app.services.forecasting_service import (
    ForecastingError,
    PREDICTION_TARGET,
    forecast_and_record,
)

router = APIRouter(
    prefix="/forecast",
    tags=["Sales Forecasting"],
)


@router.post(
    "/predict",
    response_model=ForecastResponse,
)
def create_forecast(
    payload: ForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        prediction = forecast_and_record(
            db=db,
            product_id=payload.product_id,
            user_id=current_user.user_id,
            forecast_date=payload.forecast_date,
            horizon_days=payload.horizon_days,
        )

    except ForecastingError as error:
        message = str(error)

        status_code = (
            status.HTTP_404_NOT_FOUND
            if "was not found" in message
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from error

    return ForecastResponse(
        prediction_id=prediction.prediction_id,
        product_id=prediction.product_id,
        forecast_date=prediction.forecast_date,
        horizon_days=prediction.horizon_days,
        prediction_target=PREDICTION_TARGET,
        predicted_quantity=prediction.predicted_quantity,
        model_name=prediction.model_name,
        model_version=prediction.model_version,
        predicted_at=prediction.predicted_at,
    )