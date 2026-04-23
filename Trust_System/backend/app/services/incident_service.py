from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ReportStatus
from app.db.models.report import Report
from app.schemas.incident import IncidentRead


HIGH_RISK_CATEGORIES = {
    "account abuse",
    "account takeover",
    "fraud",
    "harassment",
    "threat",
    "threats",
    "violence",
}


def _incident_conditions():
    normalized_categories = tuple(HIGH_RISK_CATEGORIES)
    return or_(
        Report.status == ReportStatus.escalated,
        func.lower(Report.category).in_(normalized_categories),
    )


def _derive_severity(report: Report) -> Literal["medium", "high", "critical"]:
    if report.status == ReportStatus.escalated:
        return "critical"

    normalized_category = (report.category or "").strip().lower()
    if normalized_category in HIGH_RISK_CATEGORIES:
        return "high"

    return "medium"


def _to_incident(report: Report) -> IncidentRead:
    return IncidentRead(
        id=report.id,
        report_id=report.id,
        subject=report.subject,
        category=report.category,
        description=report.description,
        status=report.status,
        severity=_derive_severity(report),
        reporter_id=report.reporter_id,
        reviewed_by_id=report.reviewed_by_id,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def _incident_query(limit: int, offset: int):
    return (
        select(Report)
        .where(_incident_conditions())
        .order_by(Report.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )


async def list_incidents(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[IncidentRead]:
    result = await db.execute(_incident_query(limit=limit, offset=offset))
    reports = result.scalars().all()
    return [_to_incident(report) for report in reports]


async def get_incident_or_404(db: AsyncSession, report_id: UUID) -> IncidentRead:
    result = await db.execute(
        select(Report)
        .where(Report.id == report_id)
        .where(_incident_conditions())
    )
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return _to_incident(report)
