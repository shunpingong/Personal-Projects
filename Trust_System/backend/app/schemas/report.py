from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ReportStatus


class ReportCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1)


class ReportStatusUpdate(BaseModel):
    status: ReportStatus


class ReportRead(BaseModel):
    id: UUID
    subject: str
    category: str | None
    description: str
    status: ReportStatus
    reporter_id: UUID | None
    reviewed_by_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
