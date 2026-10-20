from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.ai_service import query_text_to_sql

router = APIRouter(prefix="/ai", tags=["AI Copilot"])


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class AIQueryResponse(BaseModel):
    sql: str
    results: List[Dict[str, Any]]
    summary: str


@router.post("/query", response_model=AIQueryResponse)
def run_natural_language_query(
    payload: AIQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        data = query_text_to_sql(payload.question, db)
        return data
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Query Engine error: {str(e)}"
        )
