from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash, verify_password, create_access_token, require_user

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    full_name_he: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.TENANT
    company: Optional[str] = None
    company_he: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    full_name_he: Optional[str]
    phone: Optional[str]
    role: str
    company: Optional[str]
    company_he: Optional[str]
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        full_name_he=req.full_name_he,
        phone=req.phone,
        role=req.role,
        company=req.company,
        company_he=req.company_he,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            full_name_he=user.full_name_he, phone=user.phone,
            role=user.role.value, company=user.company,
            company_he=user.company_he, is_active=user.is_active,
            is_verified=user.is_verified,
        ),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(data={"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            full_name_he=user.full_name_he, phone=user.phone,
            role=user.role.value, company=user.company,
            company_he=user.company_he, is_active=user.is_active,
            is_verified=user.is_verified,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(require_user)):
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        full_name_he=user.full_name_he, phone=user.phone,
        role=user.role.value, company=user.company,
        company_he=user.company_he, is_active=user.is_active,
        is_verified=user.is_verified,
    )
