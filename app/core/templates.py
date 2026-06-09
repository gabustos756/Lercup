from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlmodel import Session
from app.models.user import User
from typing import Optional

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def flash(request: Request, message: str, category: str = "info"):
    """
    Store a flash message in the session.
    category can be: 'success', 'danger', 'info', 'warning'
    """
    if "flash_messages" not in request.session:
        request.session["flash_messages"] = []
    
    # Get copy of current messages, append, and re-assign to trigger session modification detection
    current_messages = list(request.session["flash_messages"])
    current_messages.append({"text": message, "type": category})
    request.session["flash_messages"] = current_messages

def render_template(request: Request, db: Session, template_name: str, context: Optional[dict] = None):
    """
    Render a Jinja2 template, injecting:
    - request
    - current_user (if logged in)
    - messages (flash messages popped from session)
    """
    if context is None:
        context = {}
        
    context["request"] = request
    
    # Check if user is logged in
    user_id = request.session.get("user_id")
    current_user = None
    if user_id and db:
        current_user = db.get(User, user_id)
    context["current_user"] = current_user
    
    # Retrieve and clear flash messages from session
    messages = request.session.pop("flash_messages", [])
    context["messages"] = messages
    
    return templates.TemplateResponse(template_name, context)
