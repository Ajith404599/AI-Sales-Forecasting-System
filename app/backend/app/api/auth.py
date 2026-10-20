from datetime import datetime, timedelta, timezone
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    get_password_hash,
    ACCESS_TOKEN_LIFETIME_MINUTES,
    decode_access_token,
    get_access_token_payload,
    oauth2_scheme,
)
from app.core.config import settings
from app.core.audit_helper import log_audit_event
from app.models.user import User, UserRole
from app.models.auth_session import AuthSession
from app.schemas.user import Token, TokenRefreshRequest, UserRead, UserSignup
from app.schemas.auth_session import AuthSessionRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _token_data(user: User, auth_session_id: Optional[int]) -> dict:
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    return {
        "sub": user.username,
        "role": role_value,
        "user_id": user.user_id,
        "token_version": user.token_version,
        "auth_session_id": auth_session_id,
    }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _as_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _close_expired_sessions(db: Session, user_id: int, now: datetime) -> None:
    sessions = db.query(AuthSession).filter(
        AuthSession.user_id == user_id,
        AuthSession.logout_at.is_(None),
    ).all()
    for auth_session in sessions:
        expires_at = _as_utc_naive(auth_session.session_expires_at)
        if expires_at <= now:
            auth_session.logout_at = expires_at
            auth_session.logout_reason = "expired"


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserSignup, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already registered")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.ANALYST,
        is_active=True,
    )
    db.add(user)
    db.flush()
    now = _utc_now()
    _close_expired_sessions(db, user.user_id, now)
    auth_session = AuthSession(
        user_id=user.user_id,
        login_at=now,
        session_expires_at=now + timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES),
    )
    db.add(auth_session)
    db.flush()
    token_data = _token_data(user, auth_session.auth_session_id)
    access_token = create_access_token(token_data)
    claims = decode_access_token(access_token)
    auth_session.session_expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc).replace(tzinfo=None)
    refresh_token = create_refresh_token(token_data)
    log_audit_event(db, user.user_id, "SIGNUP", "AUTH", f"User '{user.username}' created an account.")
    db.commit()
    db.refresh(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserRead.model_validate(user),
    }


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        or_(User.username == form_data.username, User.email == form_data.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = _utc_now()
    if user.locked_until:
        locked_until = user.locked_until
        if locked_until.tzinfo is not None:
            locked_until = locked_until.astimezone(timezone.utc).replace(tzinfo=None)
        if locked_until > now:
            remaining_seconds = max(1, int((locked_until - now).total_seconds()))
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=(
                    "Maximum login attempts reached. Your account is temporarily locked. "
                    f"Try again in {remaining_seconds} seconds."
                ),
            )
        user.locked_until = None
        user.failed_login_attempts = 0

    if not verify_password(form_data.password, user.hashed_password):
        if user.is_active:
            user.failed_login_attempts += 1
            attempts_left = max(0, settings.MAX_LOGIN_ATTEMPTS - user.failed_login_attempts)
            if attempts_left == 0:
                user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=(
                        "Maximum login attempts reached. Your account is temporarily locked. "
                        f"Try again in {settings.LOGIN_LOCKOUT_MINUTES} minutes."
                    ),
                )
            db.commit()
            attempt_word = "attempt" if attempts_left == 1 else "attempts"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid password. {attempts_left} {attempt_word} remaining.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    _close_expired_sessions(db, user.user_id, now)
    auth_session = AuthSession(
        user_id=user.user_id,
        login_at=now,
        session_expires_at=now + timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES),
    )
    db.add(auth_session)
    db.flush()
    token_data = _token_data(user, auth_session.auth_session_id)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES)

    access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    claims = decode_access_token(access_token)
    auth_session.session_expires_at = datetime.fromtimestamp(claims["exp"], timezone.utc).replace(tzinfo=None)
    refresh_token = create_refresh_token(data=token_data)

    log_audit_event(
        db=db,
        user_id=user.user_id,
        action="LOGIN",
        module="AUTH",
        description=f"User '{user.username}' successfully logged in."
    )
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserRead.model_validate(user)
    }


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    token_payload = verify_refresh_token(payload.refresh_token)
    username = token_payload.get("sub")

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated"
        )

    if token_payload.get("token_version", 0) != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")

    auth_session_id = token_payload.get("auth_session_id")
    auth_session = db.query(AuthSession).filter(
        AuthSession.auth_session_id == auth_session_id,
        AuthSession.user_id == user.user_id,
    ).first()
    if not auth_session or auth_session.logout_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication session has ended")
    now = _utc_now()
    session_expires_at = _as_utc_naive(auth_session.session_expires_at)
    if session_expires_at <= now:
        auth_session.logout_at = session_expires_at
        auth_session.logout_reason = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please sign in again.")

    token_data = _token_data(user, auth_session.auth_session_id)
    access_token_expires = session_expires_at - now

    new_access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data=token_data)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": UserRead.model_validate(user)
    }


@router.get("/history", response_model=List[AuthSessionRead])
def get_login_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _close_expired_sessions(db, current_user.user_id, _utc_now())
    db.commit()
    return db.query(AuthSession).filter(
        AuthSession.user_id == current_user.user_id,
    ).order_by(AuthSession.login_at.desc(), AuthSession.auth_session_id.desc()).limit(200).all()


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    token_payload: Dict[str, Any] = Depends(get_access_token_payload),
    db: Session = Depends(get_db),
):
    auth_session = db.query(AuthSession).filter(
        AuthSession.auth_session_id == token_payload.get("auth_session_id"),
        AuthSession.user_id == current_user.user_id,
    ).first()
    if auth_session and auth_session.logout_at is None:
        auth_session.logout_at = _utc_now()
        auth_session.logout_reason = "manual"
    current_user.token_version += 1
    db.commit()
    return {"message": "Successfully logged out"}


@router.post("/session-expired")
def close_expired_session(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    payload = decode_access_token(token, verify_expiration=False)
    expiration = payload.get("exp")
    user_id = payload.get("user_id")
    auth_session_id = payload.get("auth_session_id")
    if expiration is None or user_id is None or auth_session_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session information is unavailable")
    if float(expiration) > time.time():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session has not expired")

    auth_session = db.query(AuthSession).filter(
        AuthSession.auth_session_id == auth_session_id,
        AuthSession.user_id == user_id,
    ).first()
    if not auth_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authentication session not found")
    if auth_session.logout_at is None:
        auth_session.logout_at = _as_utc_naive(auth_session.session_expires_at)
        auth_session.logout_reason = "expired"
        db.commit()
    return {"message": "Expired session closed"}

# ============================================================
# PROFILE MANAGEMENT
# ============================================================

class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


@router.get("/profile", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserRead)
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = payload.full_name.strip()
    email = str(payload.email)
    if not name:
        raise HTTPException(status_code=422, detail="Full name cannot be blank")
    duplicate = db.query(User).filter(
        User.email == email, User.user_id != current_user.user_id
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Email already registered")

    current_user.full_name = name
    current_user.email = email
    log_audit_event(db, current_user.user_id, "PROFILE_UPDATED", "AUTH", "Account profile updated")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_my_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different")
    if len(payload.new_password.encode("utf-8")) > 72:
        raise HTTPException(status_code=422, detail="New password is too long")

    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.token_version += 1
    now = _utc_now()
    sessions = db.query(AuthSession).filter(
        AuthSession.user_id == current_user.user_id,
        AuthSession.logout_at.is_(None),
    ).all()
    for session in sessions:
        session.logout_at = now
        session.logout_reason = "password_changed"
    log_audit_event(db, current_user.user_id, "PASSWORD_CHANGED", "AUTH", "Account password changed")
    db.commit()
    return {"message": "Password updated successfully. Please sign in again."}
