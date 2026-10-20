from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


class ProductBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=150)
    category: str = Field(..., min_length=1, max_length=100)
    base_price: Decimal = Field(..., ge=0)
    description: Optional[str] = None
    active_status: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    base_price: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    active_status: Optional[bool] = None


class ProductResponse(ProductBase):
    product_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductFilter(BaseModel):
    category: Optional[str] = None
    active_status: Optional[bool] = None
    search: Optional[str] = None
