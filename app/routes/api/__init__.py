from fastapi import APIRouter
from app.routes.api.auth import router as auth_router
from app.routes.api.users import router as users_router
from app.routes.api.tournaments import router as tournaments_router

router = APIRouter(prefix="/api")
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(tournaments_router)
