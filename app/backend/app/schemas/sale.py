from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SaleCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Quantity sold must be greater than zero")
    unit_price: Optional[Decimal] = Field(None, gt=0, description="Optional override; defaults to product base price")
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    sale_date: Optional[datetime] = None


class SaleUpdate(BaseModel):
    product_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    sale_date: Optional[datetime] = None


class SaleResponse(BaseModel):
    sale_id: int
    product_id: int
    user_id: int
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    sale_date: datetime

    model_config = ConfigDict(from_attributes=True)