from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuthSessionRead(BaseModel):
    auth_session_id: int
    user_id: int
    login_at: datetime
    session_expires_at: datetime
    logout_at: Optional[datetime] = None
    logout_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
