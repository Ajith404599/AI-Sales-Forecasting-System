from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Sale(Base):
    __tablename__ = "sales"

    sale_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)
    sale_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    product = relationship("Product", back_populates="sales")
    user = relationship("User", back_populates="sales")
