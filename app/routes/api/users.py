from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.database import get_session
from app.services import UserService
from app.schemas.user import UserResponse
from typing import List, Dict, Any

router = APIRouter(prefix="/users", tags=["API Users"])

@router.get("", response_model=List[UserResponse])
def api_list_users(db: Session = Depends(get_session)):
    """API endpoint to retrieve all users."""
    return UserService.get_all_users(db)

@router.get("/profile/{user_id}", response_model=Dict[str, Any])
def api_get_profile(user_id: int, db: Session = Depends(get_session)):
    """API endpoint to get detailed stats and profile info for a user."""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    
    stats = UserService.get_user_stats(db, user_id)
    matches = UserService.get_user_matches(db, user_id)
    
    # Extract tennis profile
    tennis_profile = None
    for prof in user.profiles:
        if prof.sport == "tennis":
            tennis_profile = {
                "id": prof.id,
                "category": prof.category,
                "nickname": prof.nickname,
                "hand_preference": prof.hand_preference
            }
            break
            
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "city": user.city,
            "avatar_url": user.avatar_url,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "created_at": user.created_at
        },
        "profile": tennis_profile,
        "stats": stats,
        "matches": matches
    }
