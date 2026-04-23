from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserRole
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.report import Report


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"),
        default=UserRole.user,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    submitted_reports: Mapped[list["Report"]] = relationship(
        back_populates="reporter",
        foreign_keys="[Report.reporter_id]",
        lazy="selectin",
    )
    reviewed_reports: Mapped[list["Report"]] = relationship(
        back_populates="reviewer",
        foreign_keys="[Report.reviewed_by_id]",
        lazy="selectin",
    )
