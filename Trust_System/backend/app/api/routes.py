from fastapi import APIRouter

from app.core.config import settings
from app.modules.auth.routes import router as auth_router
from app.modules.incidents.routes import router as incidents_router
from app.modules.moderation.routes import router as moderation_router
from app.modules.reports.routes import router as reports_router
from app.modules.users.routes import router as users_router


api_router = APIRouter(prefix=settings.api_v1_prefix)


@api_router.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(reports_router)
api_router.include_router(incidents_router)
api_router.include_router(moderation_router)
