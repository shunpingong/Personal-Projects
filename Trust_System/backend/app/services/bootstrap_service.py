from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import UserRole
from app.schemas.user import UserCreate
from app.services import user_service


logger = logging.getLogger(__name__)


async def ensure_bootstrap_admin(db: AsyncSession) -> None:
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return

    existing_admin = await user_service.get_user_by_email(
        db,
        settings.bootstrap_admin_email,
    )
    if existing_admin is not None:
        return

    bootstrap_user = UserCreate(
        email=settings.bootstrap_admin_email,
        full_name=settings.bootstrap_admin_full_name,
        password=settings.bootstrap_admin_password,
        role=UserRole.admin,
        is_active=True,
    )
    await user_service.create_user(db, bootstrap_user)
    logger.info(
        "Bootstrap admin created for %s",
        settings.bootstrap_admin_email,
    )
