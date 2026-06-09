from pathlib import Path
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

STATIC_DIR = Path(__file__).resolve().parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Lercup Torneos",
    description="MVP para organización de torneos de tenis",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
def health():
    return {"status": "ok"}

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

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    https_only=(settings.ENV == "production"),
    same_site="lax",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register Web Routes
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tournaments.router)
app.include_router(formats.router)

# Register API Routes
app.include_router(api_router)
