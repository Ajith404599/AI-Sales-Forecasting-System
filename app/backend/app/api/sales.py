from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import cast, or_, String
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale
from app.schemas.sale import SaleCreate, SaleResponse, SaleUpdate
from app.core.audit_helper import log_audit_event

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def record_sale(
    sale_in: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.product_id == sale_in.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {sale_in.product_id} not found"
        )
    if not product.active_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot record sale for an inactive product"
        )

    unit_price = sale_in.unit_price if sale_in.unit_price is not None else product.base_price
    discount = sale_in.discount_amount or Decimal("0.00")
    total_amount = max(Decimal("0.00"), (Decimal(sale_in.quantity) * Decimal(unit_price)) - discount)

    new_sale = Sale(
        product_id=product.product_id,
        user_id=current_user.user_id,
        quantity=sale_in.quantity,
        unit_price=unit_price,
        discount_amount=discount,
        total_amount=total_amount,
        sale_date=sale_in.sale_date
    )
    db.add(new_sale)
    db.flush()

    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="RECORD_SALE",
        module="SALES",
        description=f"Recorded sale #{new_sale.sale_id} for product '{product.product_name}' (Qty: {new_sale.quantity}, Total: ${new_sale.total_amount})"
    )
    db.commit()
    db.refresh(new_sale)
    return new_sale


@router.get("", response_model=List[SaleResponse])
def get_sales(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    user_id: Optional[int] = Query(None, description="Filter by user/staff ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from sale timestamp"),
    end_date: Optional[datetime] = Query(None, description="Filter through sale timestamp"),
    search: Optional[str] = Query(None, min_length=1, max_length=150),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sale).join(Product, Sale.product_id == Product.product_id)
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be before end_date")
    if product_id:
        query = query.filter(Sale.product_id == product_id)
    if user_id:
        query = query.filter(Sale.user_id == user_id)
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Product.product_name.ilike(search_term),
            Product.category.ilike(search_term),
            cast(Sale.sale_id, String).ilike(search_term),
        ))

    return query.order_by(Sale.sale_date.desc()).offset(offset).limit(limit).all()


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.sale_id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
    return sale


@router.put("/{sale_id}", response_model=SaleResponse)
def update_sale(
    sale_id: int,
    sale_in: SaleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.sale_id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role not in {"admin", "manager"} and sale.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only update sales you created")

    update_data = sale_in.model_dump(exclude_unset=True, exclude_none=True)
    product_id = update_data.get("product_id", sale.product_id)
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found")
    if product_id != sale.product_id and not product.active_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot move a sale to an inactive product")

    quantity = update_data.get("quantity", sale.quantity)
    unit_price = update_data.get("unit_price", sale.unit_price)
    discount = update_data.get("discount_amount", sale.discount_amount or Decimal("0.00"))
    sale.product_id = product_id
    sale.quantity = quantity
    sale.unit_price = unit_price
    sale.discount_amount = discount
    sale.total_amount = max(Decimal("0.00"), (Decimal(quantity) * Decimal(unit_price)) - Decimal(discount))
    if "sale_date" in update_data:
        sale.sale_date = update_data["sale_date"]

    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="UPDATE_SALE",
        module="SALES",
        description=f"Updated sale #{sale.sale_id} for product '{product.product_name}'.",
    )
    db.commit()
    db.refresh(sale)
    return sale


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    sale = db.query(Sale).filter(Sale.sale_id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="DELETE_SALE",
        module="SALES",
        description=f"Deleted sale #{sale.sale_id} for product ID {sale.product_id}.",
    )
    db.delete(sale)
    db.commit()