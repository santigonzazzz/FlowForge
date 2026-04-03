import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_execution import WorkflowExecution
from app.services.workflow_executor import ExecutionResult

_STATUS_RUNNING = "running"
_STATUS_SUCCESS = "success"
_STATUS_FAILED = "failed"


class WorkflowExecutionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        workflow_id: uuid.UUID,
        input_data: dict | None = None,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> WorkflowExecution:
        """Insert a new execution record with status 'running'."""
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=_STATUS_RUNNING,
            input_data=input_data,
            retry_count=retry_count,
            max_retries=max_retries,
            started_at=datetime.now(timezone.utc),
        )
        self._db.add(execution)
        await self._db.flush()
        await self._db.refresh(execution)
        return execution

    async def mark_finished(
        self,
        execution: WorkflowExecution,
        result: ExecutionResult,
    ) -> WorkflowExecution:
        """Update the execution record with the final status and output."""
        execution.status = _STATUS_SUCCESS if result.success else _STATUS_FAILED
        execution.error_message = getattr(result, "error_message", None)
        execution.output_data = _serialize_result(result)
        execution.finished_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(execution)
        return execution

    async def get_by_workflow_id(
        self, workflow_id: uuid.UUID
    ) -> list[WorkflowExecution]:
        """Get all executions for a specific workflow, ordered by most recent first."""
        result = await self._db.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.started_at.desc())
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_result(result: ExecutionResult) -> dict:
    """Convert ExecutionResult dataclass to a JSON-serialisable dict."""
    data = asdict(result)
    # uuid.UUID is not JSON-serialisable — convert to str
    if data.get("workflow_id") is not None:
        data["workflow_id"] = str(data["workflow_id"])
    return data
