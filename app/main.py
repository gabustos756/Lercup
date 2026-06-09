from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.templates import flash
from app.core.security import NotAuthenticatedException, NotAdminException
from app.routes.web import home, auth, users, tournaments, formats
from app.routes.api import router as api_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize the database schema if running SQLite
    init_db()
    yield

app = FastAPI(
    title="Lercup Torneos",
    description="MVP para organización de torneos de tenis",
    version="1.0.0",
    lifespan=lifespan
)

# Exception handler for unauthenticated access
@app.exception_handler(NotAuthenticatedException)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedException):
    flash(request, "Debes iniciar sesión para acceder a esta página.", "warning")
    return RedirectResponse(url="/auth/login", status_code=303)

# Exception handler for unauthorized administrative access
@app.exception_handler(NotAdminException)
async def not_admin_handler(request: Request, exc: NotAdminException):
    flash(request, "Acceso denegado. Se requieren permisos de administrador.", "danger")
    return RedirectResponse(url="/", status_code=303)

# Enable Session Middleware (essential for auth sessions and flash messages)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register Web Routes
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tournaments.router)
app.include_router(formats.router)

# Register API Routes
app.include_router(api_router)

