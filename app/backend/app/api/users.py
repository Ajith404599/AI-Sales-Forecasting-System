from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role, get_password_hash, verify_password
from app.core.audit_helper import log_audit_event
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserCreate, UserUpdate, UserProfileUpdate

router = APIRouter(tags=["Users"])


@router.get("/profile", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.put("/profile", response_model=UserRead)
def update_current_user_profile(
    profile_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if profile_in.email:
        existing = db.query(User).filter(User.email == profile_in.email, User.user_id != current_user.user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        current_user.email = profile_in.email

    if profile_in.new_password:
        if not profile_in.current_password:
            raise HTTPException(status_code=400, detail="Current password required to set new password")
        if not verify_password(profile_in.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid current password")
        current_user.hashed_password = get_password_hash(profile_in.new_password)

    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="UPDATE_PROFILE",
        module="USERS",
        description=f"User '{current_user.username}' updated profile settings."
    )
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/users", response_model=List[UserRead])
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    return db.query(User).order_by(User.user_id.asc()).offset(offset).limit(limit).all()


@router.get("/users/{user_id}", response_model=UserRead)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    role_enum_val = UserRole(user_in.role.value if hasattr(user_in.role, "value") else str(user_in.role).lower())

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=role_enum_val,
        is_active=user_in.is_active
    )
    db.add(new_user)
    db.flush()

    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="CREATE_USER",
        module="USERS",
        description=f"Admin created user '{new_user.username}' with role '{new_user.role.value}'"
    )
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/users/{user_id}", response_model=UserRead)
def update_user_by_admin(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.email:
        existing = db.query(User).filter(User.email == user_in.email, User.user_id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        user.email = user_in.email

    if user_in.role is not None:
        role_val = user_in.role.value if hasattr(user_in.role, "value") else str(user_in.role).lower()
        user.role = UserRole(role_val)

    if user_in.is_active is not None:
        user.is_active = user_in.is_active

    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)

    log_audit_event(
        db=db,
        user_id=current_user.user_id,
        action="ADMIN_UPDATE_USER",
        module="USERS",
        description=f"Admin updated user '{user.username}' (ID: {user.user_id})"
    )
    db.commit()
    db.refresh(user)
    return user