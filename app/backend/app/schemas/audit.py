from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    action: str
    module: str
    description: str


class AuditLogCreate(AuditLogBase):
    user_id: int


class AuditLogResponse(AuditLogBase):
    log_id: int
    user_id: int
    username: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
