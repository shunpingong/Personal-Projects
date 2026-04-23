from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.modules.auth.dependencies import require_roles
from app.schemas.incident import IncidentRead
from app.services import incident_service


router = APIRouter(prefix="/incidents", tags=["incidents"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
ModeratorUser = Annotated[
    User,
    Depends(require_roles(UserRole.admin, UserRole.moderator)),
]


@router.get("/", response_model=list[IncidentRead])
async def list_incidents(
    db: DbSession,
    _: ModeratorUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[IncidentRead]:
    return await incident_service.list_incidents(db, limit=limit, offset=offset)


@router.get("/{report_id}", response_model=IncidentRead)
async def get_incident(
    report_id: UUID,
    db: DbSession,
    _: ModeratorUser,
) -> IncidentRead:
    return await incident_service.get_incident_or_404(db, report_id)
