import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings, database_url_for_log
from app.core.database import engine, init_db
from app.core.templates import flash
from app.core.security import NotAuthenticatedException, NotAdminException
from app.routes.web import home, auth, users, tournaments, formats, matches, notifications
from app.routes.api import router as api_router
from contextlib import asynccontextmanager

STATIC_DIR = Path(__file__).resolve().parent / "static"

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    css_path = STATIC_DIR / "css" / "app.css"
    css_info = f"{css_path.stat().st_size} bytes" if css_path.exists() else "MISSING"
    logger.info(
        "Startup: env=%s db_dialect=%s db_url=%s static_css=%s",
        settings.ENV,
        engine.dialect.name,
        database_url_for_log(settings.DATABASE_URL),
        css_info,
    )
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

# Register Web Routes
app.include_router(home.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tournaments.router)
app.include_router(formats.router)
app.include_router(matches.router)
app.include_router(notifications.router)

# Register API Routes
app.include_router(api_router)

# Static files last (FastAPI/Starlette routing order)
css_path = STATIC_DIR / "css" / "app.css"
if css_path.exists():
    logger.info("Static assets: dir=%s css_bytes=%s", STATIC_DIR, css_path.stat().st_size)
else:
    logger.warning("Static assets missing: %s", css_path)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
