from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    module: Optional[str] = Query(None, description="Filter by module"),
    action: Optional[str] = Query(None, description="Filter by action"),
    start_date: Optional[datetime] = Query(None, description="Filter from created_at"),
    end_date: Optional[datetime] = Query(None, description="Filter until created_at"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    query = db.query(
        AuditLog.log_id,
        AuditLog.user_id,
        AuditLog.action,
        AuditLog.module,
        AuditLog.description,
        AuditLog.created_at,
        User.username.label("username")
    ).outerjoin(User, AuditLog.user_id == User.user_id)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return [
        AuditLogResponse(
            log_id=log.log_id,
            user_id=log.user_id,
            username=log.username or "Unknown/Deleted User",
            action=log.action,
            module=log.module,
            description=log.description,
            created_at=log.created_at
        )
        for log in logs
    ]


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    log_record = db.query(
        AuditLog.log_id,
        AuditLog.user_id,
        AuditLog.action,
        AuditLog.module,
        AuditLog.description,
        AuditLog.created_at,
        User.username.label("username")
    ).outerjoin(User, AuditLog.user_id == User.user_id).filter(AuditLog.log_id == log_id).first()

    if not log_record:
        raise HTTPException(status_code=404, detail="Audit log entry not found")

    return AuditLogResponse(
        log_id=log_record.log_id,
        user_id=log_record.user_id,
        username=log_record.username or "Unknown/Deleted User",
        action=log_record.action,
        module=log_record.module,
        description=log_record.description,
        created_at=log_record.created_at
    )
