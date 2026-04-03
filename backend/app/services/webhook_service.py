import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.workflow_execution_repository import (
    WorkflowExecutionRepository,
)
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.workflow import ExecutionStepResult, WebhookTriggerResponse, WebhookQueuedResponse
from app.services.workflow_executor import WorkflowExecutor
from app.services.queue_service import QueueService

_TRIGGER_TYPE = "webhook"


class WebhookService:
    def __init__(self, db: AsyncSession, queue_service: QueueService | None = None) -> None:
        self._repo = WorkflowRepository(db)
        self._execution_repo = WorkflowExecutionRepository(db)
        self._executor = WorkflowExecutor()
        self._queue_service = queue_service

    async def _validate_webhook_trigger(self, workflow_id: uuid.UUID):
        """Re-usable workflow validation logic for both sync and async triggers."""
        # 1. Fetch workflow
        workflow = await self._repo.get_by_id(workflow_id)
        if workflow is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found.",
            )

        # 2. Validate it accepts webhook triggers
        trigger = workflow.definition.get("trigger", {})
        if trigger.get("type") != _TRIGGER_TYPE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Workflow {workflow_id} does not have a webhook trigger. "
                    f"Expected trigger.type='webhook', "
                    f"got '{trigger.get('type', '<missing>')}'."
                ),
            )

        # 3. Validate workflow is active
        if not workflow.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workflow {workflow_id} is inactive and cannot be triggered.",
            )
            
        return workflow

    async def trigger_async(
        self,
        workflow_id: uuid.UUID,
        payload: dict,
    ) -> WebhookQueuedResponse:
        workflow = await self._validate_webhook_trigger(workflow_id)
        
        if not self._queue_service:
            raise RuntimeError("QueueService not initialized.")
            
        await self._queue_service.enqueue_workflow(workflow.id, payload)
        return WebhookQueuedResponse(status="queued")

    async def trigger(
        self,
        workflow_id: uuid.UUID,
        payload: dict,
    ) -> WebhookTriggerResponse:
        workflow = await self._validate_webhook_trigger(workflow_id)

        # 4. Create execution record with input_data
        execution = await self._execution_repo.create(
            workflow_id=workflow.id,
            input_data=payload,
        )

        # 5. Execute passing the incoming payload as input_data (available via {{input.*}})
        result = self._executor.run(
            definition=workflow.definition,
            workflow_id=workflow.id,
            input_data=payload,
        )

        # 6. Update execution record with result
        await self._execution_repo.mark_finished(execution, result)

        # 5. Map to response schema
        return WebhookTriggerResponse(
            workflow_id=workflow.id,
            success=result.success,
            steps_total=result.steps_total,
            steps_executed=result.steps_executed,
            response=result.response,
            payload=payload,
            results=[
                ExecutionStepResult(
                    step_index=r.step_index,
                    step_type=r.step_type,
                    success=r.success,
                    output=r.output,
                    error=r.error,
                )
                for r in result.results
            ],
        )
