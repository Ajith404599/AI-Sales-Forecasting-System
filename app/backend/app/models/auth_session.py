from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        Index("idx_auth_sessions_user_login", "user_id", "login_at"),
        Index("idx_auth_sessions_logout", "logout_at"),
    )

    auth_session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    login_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    session_expires_at = Column(DateTime(timezone=True), nullable=False)
    logout_at = Column(DateTime(timezone=True), nullable=True)
    logout_reason = Column(String(20), nullable=True)

    user = relationship("User", back_populates="auth_sessions")
