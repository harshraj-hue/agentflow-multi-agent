"""Workflow database model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.artifact import ArtifactModel
    from app.models.event import ExecutionEventModel
    from app.models.task import TaskModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class WorkflowModel(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    tasks: Mapped[list[TaskModel]] = relationship(  # type: ignore[name-defined]
        "TaskModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="TaskModel.order_index",
    )
    events: Mapped[list[ExecutionEventModel]] = relationship(  # type: ignore[name-defined]
        "ExecutionEventModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="ExecutionEventModel.created_at",
    )
    artifacts: Mapped[list[ArtifactModel]] = relationship(  # type: ignore[name-defined]
        "ArtifactModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="ArtifactModel.created_at",
    )
