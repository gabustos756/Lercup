from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from app.core.database import get_session
from app.core.templates import render_template, flash
from app.services import AuthService
from app.schemas.user import UserCreate

router = APIRouter(prefix="/auth")

@router.get("/login")
def get_login(request: Request, db: Session = Depends(get_session)):
    """Render the login form."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)
    return render_template(request, db, "auth/login.html")

@router.post("/login")
def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    """Process user login form."""
    user = AuthService.authenticate_user(db, email, password)
    if not user:
        flash(request, "Correo electrónico o contraseña incorrectos.", "danger")
        return render_template(request, db, "auth/login.html", {"email": email})
    
    # Store user ID in session
    request.session["user_id"] = user.id
    flash(request, f"¡Bienvenido de nuevo, {user.full_name}!", "success")
    return RedirectResponse(url=f"/users/profile/{user.id}", status_code=303)

@router.get("/register")
def get_register(request: Request, db: Session = Depends(get_session)):
    """Render the registration form."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=303)
    return render_template(request, db, "auth/register.html")

@router.post("/register")
def post_register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_session)
):
    """Process user registration form."""
    if password != confirm_password:
        flash(request, "Las contraseñas no coinciden.", "danger")
        return render_template(request, db, "auth/register.html", {"full_name": full_name, "email": email})
    
    try:
        user_data = UserCreate(email=email, full_name=full_name, password=password, is_admin=False)
        AuthService.register_user(db, user_data)
        flash(request, "Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return RedirectResponse(url="/auth/login", status_code=303)
    except ValueError as e:
        flash(request, str(e), "danger")
        return render_template(request, db, "auth/register.html", {"full_name": full_name, "email": email})

@router.get("/logout")
def logout(request: Request):
    """Clear session data and logout."""
    request.session.clear()
    flash(request, "Has cerrado sesión correctamente.", "info")
    return RedirectResponse(url="/", status_code=303)
