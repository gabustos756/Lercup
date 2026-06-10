from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from app.core.database import get_session
from app.core.templates import render_template, flash
from app.models.user import User
from app.services import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_current_user_or_redirect, require_admin
from typing import Optional

router = APIRouter(prefix="/users")

@router.get("")
def list_users(
    request: Request, 
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect)
):
    """List all registered users (Requires login)."""
    users = UserService.get_all_users(db)
    return render_template(request, db, "users/list.html", {
        "users": users,
        "active_page": "users"
    })

@router.get("/profile/edit")
def get_edit_self_profile(
    request: Request,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect)
):
    """Render self-profile edit form (Any logged-in user)."""
    # Locate tennis profile settings
    tennis_profile = None
    for prof in current_user.profiles:
        if prof.sport == "tennis":
            tennis_profile = prof
            break
            
    category = tennis_profile.category if tennis_profile else "B2"
    nickname = tennis_profile.nickname if tennis_profile else ""
    hand_preference = tennis_profile.hand_preference if tennis_profile else "right"
    
    return render_template(request, db, "users/profile_edit.html", {
        "user": current_user,
        "category": category,
        "nickname": nickname,
        "hand_preference": hand_preference,
        "active_page": "profile"
    })

@router.post("/profile/edit")
def post_edit_self_profile(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    city: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    avatar_url: Optional[str] = Form(None),
    category: str = Form("B2"),
    nickname: Optional[str] = Form(None),
    hand_preference: str = Form("right"),
    password: Optional[str] = Form(""),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect)
):
    """Process self-profile modifications (Any logged-in user)."""
    try:
        user_data = UserUpdate(
            email=email,
            full_name=full_name,
            city=city if city and city.strip() != "" else None,
            phone_number=phone_number if phone_number and phone_number.strip() != "" else None,
            avatar_url=avatar_url if avatar_url and avatar_url.strip() != "" else None,
            password=password if password and password.strip() != "" else None,
            role=current_user.role,
            is_admin=current_user.is_admin
        )
        UserService.update_user(
            db, 
            current_user.id, 
            user_data, 
            category=category, 
            nickname=nickname if nickname and nickname.strip() != "" else None,
            hand_preference=hand_preference
        )
        flash(request, "Tu perfil ha sido actualizado con éxito.", "success")
        return RedirectResponse(url=f"/users/profile/{current_user.id}", status_code=303)
    except ValueError as e:
        flash(request, str(e), "danger")
        return render_template(request, db, "users/profile_edit.html", {
            "user": current_user,
            "category": category,
            "nickname": nickname,
            "hand_preference": hand_preference,
            "active_page": "profile"
        })

@router.get("/profile/{user_id}")
def user_profile(
    user_id: int, 
    request: Request, 
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_or_redirect)
):
    """Render player profile showing match history and calculated performance metrics (Requires login)."""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        flash(request, "Usuario no encontrado.", "danger")
        return RedirectResponse(url="/users", status_code=303)
    
    stats = UserService.get_user_stats(db, user_id)
    upcoming_matches = UserService.get_user_upcoming_matches(db, user_id)
    played_matches = UserService.get_user_played_matches(db, user_id)
    is_own_profile = current_user.id == user_id
    
    # Set active_page navigation highlighting
    active_page = "profile" if current_user.id == user_id else "users"
    
    # Extract player profile characteristics
    tennis_profile = None
    for prof in user.profiles:
        if prof.sport == "tennis":
            tennis_profile = prof
            break
            
    return render_template(request, db, "users/profile.html", {
        "user": user,
        "profile": tennis_profile,
        "stats": stats,
        "upcoming_matches": upcoming_matches,
        "played_matches": played_matches,
        "is_own_profile": is_own_profile,
        "active_page": active_page
    })

@router.get("/create")
def get_create_user(
    request: Request, 
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin)
):
    """Render the user creation form (Admin only)."""
    return render_template(request, db, "users/form.html", {
        "edit_mode": False,
        "active_page": "users"
    })

@router.post("/create")
def post_create_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    city: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    avatar_url: Optional[str] = Form(None),
    category: str = Form("B2"),
    nickname: Optional[str] = Form(None),
    hand_preference: str = Form("right"),
    role: str = Form("player"),
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin)
):
    """Process user creation form (Admin only)."""
    try:
        user_data = UserCreate(
            email=email,
            full_name=full_name,
            city=city if city and city.strip() != "" else None,
            phone_number=phone_number if phone_number and phone_number.strip() != "" else None,
            avatar_url=avatar_url if avatar_url and avatar_url.strip() != "" else None,
            password=password,
            role=role,
            is_admin=True if role == "admin" else False
        )
        UserService.create_user(
            db, 
            user_data, 
            category=category, 
            nickname=nickname if nickname and nickname.strip() != "" else None,
            hand_preference=hand_preference
        )
        flash(request, f"Usuario '{full_name}' creado con éxito.", "success")
        return RedirectResponse(url="/users", status_code=303)
    except ValueError as e:
        flash(request, str(e), "danger")
        return render_template(request, db, "users/form.html", {
            "edit_mode": False,
            "full_name": full_name,
            "email": email,
            "city": city,
            "phone_number": phone_number,
            "avatar_url": avatar_url,
            "category": category,
            "nickname": nickname,
            "hand_preference": hand_preference,
            "role": role,
            "active_page": "users"
        })

@router.get("/edit/{user_id}")
def get_edit_user(
    user_id: int, 
    request: Request, 
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin)
):
    """Render user edit form (Admin only)."""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        flash(request, "Usuario no encontrado.", "danger")
        return RedirectResponse(url="/users", status_code=303)
    
    # Locate tennis profile settings
    tennis_profile = None
    for prof in user.profiles:
        if prof.sport == "tennis":
            tennis_profile = prof
            break
            
    category = tennis_profile.category if tennis_profile else "B2"
    nickname = tennis_profile.nickname if tennis_profile else ""
    hand_preference = tennis_profile.hand_preference if tennis_profile else "right"
        
    return render_template(request, db, "users/form.html", {
        "edit_mode": True,
        "user": user,
        "category": category,
        "nickname": nickname,
        "hand_preference": hand_preference,
        "active_page": "users"
    })

@router.post("/edit/{user_id}")
def post_edit_user(
    user_id: int,
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    city: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    avatar_url: Optional[str] = Form(None),
    category: str = Form("B2"),
    nickname: Optional[str] = Form(None),
    hand_preference: str = Form("right"),
    password: Optional[str] = Form(""),
    role: str = Form("player"),
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin)
):
    """Process user modifications (Admin only)."""
    try:
        user_data = UserUpdate(
            email=email,
            full_name=full_name,
            city=city if city and city.strip() != "" else None,
            phone_number=phone_number if phone_number and phone_number.strip() != "" else None,
            avatar_url=avatar_url if avatar_url and avatar_url.strip() != "" else None,
            password=password if password and password.strip() != "" else None,
            role=role,
            is_admin=True if role == "admin" else False
        )
        UserService.update_user(
            db, 
            user_id, 
            user_data, 
            category=category, 
            nickname=nickname if nickname and nickname.strip() != "" else None,
            hand_preference=hand_preference
        )
        flash(request, f"Usuario '{full_name}' actualizado con éxito.", "success")
        return RedirectResponse(url="/users", status_code=303)
    except ValueError as e:
        flash(request, str(e), "danger")
        user = UserService.get_user_by_id(db, user_id)
        return render_template(request, db, "users/form.html", {
            "edit_mode": True,
            "user": user,
            "category": category,
            "nickname": nickname,
            "hand_preference": hand_preference,
            "active_page": "users"
        })

@router.post("/delete/{user_id}")
def post_delete_user(
    user_id: int, 
    request: Request, 
    db: Session = Depends(get_session),
    admin_user: User = Depends(require_admin)
):
    """Delete user (Admin only)."""
    # Prevent deletion of oneself
    if admin_user.id == user_id:
        flash(request, "No puedes eliminar tu propio usuario.", "danger")
        return RedirectResponse(url="/users", status_code=303)
        
    success = UserService.delete_user(db, user_id)
    if success:
        flash(request, "Usuario eliminado correctamente.", "success")
    else:
        flash(request, "El usuario no pudo ser eliminado.", "danger")
        
    return RedirectResponse(url="/users", status_code=303)

