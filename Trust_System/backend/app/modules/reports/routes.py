from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ReportStatus, UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user, require_roles
from app.schemas.report import ReportCreate, ReportRead, ReportStatusUpdate
from app.services import moderation_service


router = APIRouter(prefix="/reports", tags=["reports"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ModeratorUser = Annotated[
    User,
    Depends(require_roles(UserRole.admin, UserRole.moderator)),
]


@router.post("/", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ReportRead:
    return await moderation_service.create_report(db, current_user, payload)


@router.get("/", response_model=list[ReportRead])
async def list_reports(
    db: DbSession,
    _: ModeratorUser,
    status_filter: ReportStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReportRead]:
    return await moderation_service.list_reports(
        db,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ReportRead:
    report = await moderation_service.get_report_or_404(db, report_id)

    if current_user.role not in {UserRole.admin, UserRole.moderator}:
        if report.reporter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

    return report


@router.patch("/{report_id}/status", response_model=ReportRead)
async def update_report_status(
    report_id: UUID,
    payload: ReportStatusUpdate,
    db: DbSession,
    current_user: ModeratorUser,
) -> ReportRead:
    return await moderation_service.update_report_status(
        db,
        report_id,
        payload,
        current_user,
    )
