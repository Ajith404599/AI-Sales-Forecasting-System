from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.core.audit_helper import log_audit_event
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = Query(None, description="Filter by product category"),
    active_status: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if active_status is not None:
        query = query.filter(Product.active_status == active_status)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Product.product_name.ilike(search_fmt),
                Product.description.ilike(search_fmt)
            )
        )
    return query.order_by(Product.product_id.desc()).offset(offset).limit(limit).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    product = Product(
        product_name=product_in.product_name,
        category=product_in.category,
        base_price=product_in.base_price,
        description=product_in.description,
        active_status=product_in.active_status
    )
    db.add(product)
    db.flush()

    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="CREATE_PRODUCT",
        module="PRODUCTS",
        description=f"Created product '{product.product_name}' (ID: {product.product_id}, Price: ${product.base_price})"
    )
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="UPDATE_PRODUCT",
        module="PRODUCTS",
        description=f"Updated product ID {product.product_id} ('{product.product_name}')"
    )
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", response_model=ProductResponse)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    product.active_status = False
    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="SOFT_DELETE_PRODUCT",
        module="PRODUCTS",
        description=f"Deactivated product ID {product.product_id} ('{product.product_name}')"
    )
    db.commit()
    db.refresh(product)
    return product