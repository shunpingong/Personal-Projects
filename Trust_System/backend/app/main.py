from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.security import JWTContextMiddleware
from app.db.session import AsyncSessionFactory
from app.services import bootstrap_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with AsyncSessionFactory() as session:
        await bootstrap_service.ensure_bootstrap_admin(session)
    yield


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.project_name,
        version="1.0.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(JWTContextMiddleware)
    application.include_router(api_router)
    return application


app = create_application()
