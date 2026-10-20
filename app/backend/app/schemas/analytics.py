from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal


class AnalyticsSummary(BaseModel):
    total_sales_count: int
    total_revenue: float
    total_quantity_sold: int
    average_order_value: float
    active_products_count: int
    total_users_count: int


class MonthlySalesItem(BaseModel):
    month: str
    total_orders: int
    total_quantity: int
    total_revenue: float


class ProductPerformanceItem(BaseModel):
    product_id: int
    product_name: str
    category: str
    base_price: float
    total_quantity_sold: int
    total_revenue: float


class CategoryPerformanceItem(BaseModel):
    category: str
    total_products: int
    total_quantity_sold: int
    total_revenue: float
