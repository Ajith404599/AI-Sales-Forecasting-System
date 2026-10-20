from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_audit_event(db: Session, user_id: int, action: str, module: str, description: str):
    """Appends an audit log entry to the active transaction."""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            module=module,
            description=description
        )
        db.add(log_entry)
        db.flush()
    except Exception as e:
        print(f"Error appending audit log: {e}")