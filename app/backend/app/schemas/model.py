from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ModelRunRead(BaseModel):
    model_run_id: int
    model_name: str
    model_version: str
    prediction_target: str
    training_records: int
    evaluation_records: int
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    trained_at: datetime
    artifact_path: Optional[str] = None
    is_active: bool
    training_status: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CandidateResult(BaseModel):
    model_name: str
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    training_status: str
    error_message: Optional[str] = None


class TrainingResponse(BaseModel):
    training_status: str
    model_version: str
    selected_model: Optional[str] = None
    training_records: int = 0
    evaluation_records: int = 0
    trained_at: datetime
    candidates: List[CandidateResult] = []
    error_message: Optional[str] = None