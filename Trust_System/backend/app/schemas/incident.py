from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import ReportStatus


class IncidentRead(BaseModel):
    id: UUID
    report_id: UUID
    subject: str
    category: str | None
    description: str
    status: ReportStatus
    severity: Literal["medium", "high", "critical"]
    reporter_id: UUID | None
    reviewed_by_id: UUID | None
    created_at: datetime
    updated_at: datetime
