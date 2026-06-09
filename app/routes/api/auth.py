from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.database import get_session
from app.services import AuthService
from app.schemas.user import UserCreate, UserResponse
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["API Auth"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def api_register(user_data: UserCreate, db: Session = Depends(get_session)):
    """Register a new player/user via JSON API."""
    try:
        return AuthService.register_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def api_login(credentials: LoginRequest, db: Session = Depends(get_session)):
    """Authenticate user and return a placeholder JWT or session indicator."""
    user = AuthService.authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Credenciales incorrectas."
        )
    return TokenResponse(
        access_token=f"placeholder_token_for_user_{user.id}",
        token_type="bearer"
    )
