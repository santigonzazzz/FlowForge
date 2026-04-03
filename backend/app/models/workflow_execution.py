import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Integer, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="'success' or 'failed'",
    )
    input_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="External data passed to the executor (e.g. webhook payload)",
    )
    output_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Serialised ExecutionResult returned by the executor",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times this execution has been retried",
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Maximum allowed retries for this execution",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="The top-level error message if the workflow failed fatally",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship (lazy select — load only when accessed)
    workflow: Mapped["Workflow"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Workflow",
        back_populates="executions",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowExecution id={self.id} "
            f"workflow_id={self.workflow_id} status={self.status!r}>"
        )
