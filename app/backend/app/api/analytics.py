from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale
from app.schemas.analytics import (
    AnalyticsSummary,
    MonthlySalesItem,
    ProductPerformanceItem,
    CategoryPerformanceItem
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sales_stats = db.query(
        func.count(Sale.sale_id).label("total_orders"),
        func.coalesce(func.sum(Sale.quantity), 0).label("total_quantity"),
        func.coalesce(func.sum(Sale.total_amount), 0.0).label("total_revenue")
    ).first()

    total_orders = sales_stats.total_orders or 0
    total_quantity = int(sales_stats.total_quantity or 0)
    total_revenue = float(sales_stats.total_revenue or 0.0)
    avg_order_val = (total_revenue / total_orders) if total_orders > 0 else 0.0

    active_products = db.query(func.count(Product.product_id)).filter(Product.active_status.is_(True)).scalar() or 0
    total_users = db.query(func.count(User.user_id)).scalar() or 0

    return AnalyticsSummary(
        total_sales_count=total_orders,
        total_revenue=round(total_revenue, 2),
        total_quantity_sold=total_quantity,
        average_order_value=round(avg_order_val, 2),
        active_products_count=active_products,
        total_users_count=total_users
    )


@router.get("/monthly", response_model=List[MonthlySalesItem])
def get_monthly_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        dialect = db.get_bind().dialect.name
    except Exception:
        dialect = db.bind.dialect.name if db.bind else "mysql"

    if dialect == "sqlite":
        date_group = func.strftime("%Y-%m", Sale.sale_date)
    elif dialect == "postgresql":
        date_group = func.to_char(Sale.sale_date, "YYYY-MM")
    else:
        date_group = func.date_format(Sale.sale_date, "%Y-%m")

    results = db.query(
        date_group.label("month"),
        func.count(Sale.sale_id).label("total_orders"),
        func.coalesce(func.sum(Sale.quantity), 0).label("total_quantity"),
        func.coalesce(func.sum(Sale.total_amount), 0.0).label("total_revenue")
    ).group_by(date_group).order_by(date_group.asc()).all()

    return [
        MonthlySalesItem(
            month=str(row.month or "Unknown"),
            total_orders=row.total_orders or 0,
            total_quantity=int(row.total_quantity or 0),
            total_revenue=round(float(row.total_revenue or 0.0), 2)
        )
        for row in results if row.month is not None
    ]


@router.get("/products", response_model=List[ProductPerformanceItem])
def get_products_performance(
    sort_by: str = Query("revenue_desc", enum=["revenue_desc", "revenue_asc", "volume_desc", "volume_asc"]),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rev_expr = func.coalesce(func.sum(Sale.total_amount), 0.0)
    qty_expr = func.coalesce(func.sum(Sale.quantity), 0)

    query = db.query(
        Product.product_id,
        Product.product_name,
        Product.category,
        Product.base_price,
        qty_expr.label("total_quantity_sold"),
        rev_expr.label("total_revenue")
    ).outerjoin(Sale, Product.product_id == Sale.product_id).group_by(
        Product.product_id, Product.product_name, Product.category, Product.base_price
    )

    if sort_by == "revenue_desc":
        query = query.order_by(desc(rev_expr))
    elif sort_by == "revenue_asc":
        query = query.order_by(asc(rev_expr))
    elif sort_by == "volume_desc":
        query = query.order_by(desc(qty_expr))
    elif sort_by == "volume_asc":
        query = query.order_by(asc(qty_expr))

    results = query.limit(limit).all()

    return [
        ProductPerformanceItem(
            product_id=row.product_id,
            product_name=row.product_name,
            category=row.category,
            base_price=float(row.base_price),
            total_quantity_sold=int(row.total_quantity_sold),
            total_revenue=round(float(row.total_revenue), 2)
        )
        for row in results
    ]


@router.get("/categories", response_model=List[CategoryPerformanceItem])
def get_categories_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rev_expr = func.coalesce(func.sum(Sale.total_amount), 0.0)
    qty_expr = func.coalesce(func.sum(Sale.quantity), 0)

    results = db.query(
        Product.category,
        func.count(func.distinct(Product.product_id)).label("total_products"),
        qty_expr.label("total_quantity_sold"),
        rev_expr.label("total_revenue")
    ).outerjoin(Sale, Product.product_id == Sale.product_id).group_by(
        Product.category
    ).order_by(desc(rev_expr)).all()

    return [
        CategoryPerformanceItem(
            category=row.category,
            total_products=row.total_products,
            total_quantity_sold=int(row.total_quantity_sold),
            total_revenue=round(float(row.total_revenue), 2)
        )
        for row in results
    ]
