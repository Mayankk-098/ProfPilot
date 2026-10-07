import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import Lecturer
from app.models.academic import User
from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _initials(name: str) -> str:
    parts = [
        part
        for part in re.split(r"\s+", name.strip())
        if part
    ]

    if not parts:
        return "L"

    if len(parts) == 1:
        return parts[0][0].upper()

    return (
        f"{parts[0][0]}{parts[-1][0]}"
    ).upper()


def _new_lecturer_id() -> str:
    return f"lec_{uuid.uuid4().hex[:12]}"


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = str(data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    existing_lecturer = db.scalar(
        select(Lecturer).where(Lecturer.email == email)
    )
    if existing_lecturer is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A lecturer with this email already exists.",
        )

    lecturer = Lecturer(
        id=_new_lecturer_id(),
        name=data.name.strip(),
        initials=_initials(data.name),
        title=data.title.strip(),
        department=data.department.strip(),
        email=email,
        experience=0,
    )

    db.add(lecturer)
    db.flush()

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        lecturer_id=lecturer.id,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with these details already exists.",
        ) from error

    db.refresh(user)

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
    }


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        str(data.email).strip().lower(),
        data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def get_me(
    current_user=Depends(get_current_user),
):
    lecturer = current_user.lecturer

    return {
        "id": current_user.id,
        "email": current_user.email,
        "lecturer_id": current_user.lecturer_id,
        "name": lecturer.name,
        "title": lecturer.title,
        "department": lecturer.department,
    }
