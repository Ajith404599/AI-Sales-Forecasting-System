from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PredictionHistory(Base):
    __tablename__ = "prediction_history"
    __table_args__ = (
        Index("idx_prediction_product_date", "product_id", "forecast_date"),
        Index("idx_prediction_user_time", "user_id", "predicted_at"),
        Index("idx_prediction_model_version", "model_version"),
    )

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    model_run_id = Column(Integer, ForeignKey("model_runs.model_run_id", ondelete="RESTRICT"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="SET NULL"), nullable=True)
    forecast_date = Column(Date, nullable=False)
    horizon_days = Column(Integer, nullable=False)
    predicted_quantity = Column(Numeric(14, 4), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(64), nullable=False)
    predicted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    actual_quantity = Column(Numeric(14, 4), nullable=True)

    model_run = relationship("ModelRun", back_populates="predictions")