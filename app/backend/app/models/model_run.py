from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ModelRun(Base):
    __tablename__ = "model_runs"
    __table_args__ = (
        UniqueConstraint("model_name", "model_version", name="uq_model_runs_name_version"),
        Index("idx_model_runs_active_trained", "is_active", "trained_at"),
    )

    model_run_id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(64), nullable=False)
    prediction_target = Column(String(64), nullable=False)
    training_records = Column(Integer, nullable=False, default=0)
    evaluation_records = Column(Integer, nullable=False, default=0)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    r2 = Column(Float, nullable=True)
    trained_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    artifact_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    training_status = Column(String(20), nullable=False, default="pending", index=True)
    error_message = Column(Text, nullable=True)

    predictions = relationship("PredictionHistory", back_populates="model_run")