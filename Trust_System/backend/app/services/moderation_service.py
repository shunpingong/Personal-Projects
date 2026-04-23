from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ReportStatus
from app.db.models.report import Report
from app.db.models.user import User
from app.schemas.report import ReportCreate, ReportStatusUpdate


async def create_report(
    db: AsyncSession,
    reporter: User,
    payload: ReportCreate,
) -> Report:
    report = Report(
        subject=payload.subject,
        category=payload.category,
        description=payload.description,
        reporter_id=reporter.id,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def list_reports(
    db: AsyncSession,
    *,
    status_filter: ReportStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Report]:
    statement = (
        select(Report)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if status_filter is not None:
        statement = statement.where(Report.status == status_filter)

    result = await db.execute(statement)
    return result.scalars().all()


async def get_report_or_404(db: AsyncSession, report_id: UUID) -> Report:
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report


async def update_report_status(
    db: AsyncSession,
    report_id: UUID,
    payload: ReportStatusUpdate,
    reviewer: User,
) -> Report:
    report = await get_report_or_404(db, report_id)
    report.status = payload.status
    report.reviewed_by_id = reviewer.id

    await db.commit()
    await db.refresh(report)
    return report
