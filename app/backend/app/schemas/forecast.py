from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ForecastRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    forecast_date: Optional[date] = None
    horizon_days: Optional[int] = Field(None, ge=1, le=90)

    @model_validator(mode="after")
    def require_one_horizon_input(self):
        if (self.forecast_date is None) == (self.horizon_days is None):
            raise ValueError("Provide exactly one of forecast_date or horizon_days")
        return self


class ForecastResponse(BaseModel):
    prediction_id: int
    product_id: int
    forecast_date: date
    horizon_days: int
    prediction_target: str
    predicted_quantity: Decimal
    model_name: str
    model_version: str
    predicted_at: datetime


class PredictionRead(BaseModel):
    prediction_id: int
    model_run_id: int
    product_id: Optional[int] = None
    forecast_date: date
    horizon_days: int
    predicted_quantity: Decimal
    model_name: str
    model_version: str
    predicted_at: datetime
    user_id: int
    actual_quantity: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class ActualQuantityUpdate(BaseModel):
    actual_quantity: Decimal = Field(..., ge=0)