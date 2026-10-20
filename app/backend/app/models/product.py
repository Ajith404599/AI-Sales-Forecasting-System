from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    base_price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    active_status = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sales = relationship("Sale", back_populates="product")
