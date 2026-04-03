import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.workflow_execution_repository import (
    WorkflowExecutionRepository,
)
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.workflow import (
    ExecutionResponse,
    ExecutionStepResult,
    WorkflowCreate,
    WorkflowExecutionResponse,
    WorkflowResponse,
)
from app.services.workflow_executor import WorkflowExecutor


class WorkflowService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = WorkflowRepository(db)
        self._execution_repo = WorkflowExecutionRepository(db)
        self._executor = WorkflowExecutor()

    async def create_workflow(self, data: WorkflowCreate) -> WorkflowResponse:
        workflow = await self._repo.create(data)
        return WorkflowResponse.model_validate(workflow)

    async def list_workflows(self) -> list[WorkflowResponse]:
        workflows = await self._repo.get_all()
        return [WorkflowResponse.model_validate(w) for w in workflows]

    async def execute_workflow(
        self, 
        workflow_id: uuid.UUID, 
        input_data: dict | None = None,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> ExecutionResponse:
        workflow = await self._repo.get_by_id(workflow_id)

        if workflow is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found.",
            )

        if not workflow.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workflow {workflow_id} is inactive and cannot be executed.",
            )

        execution = await self._execution_repo.create(
            workflow_id=workflow.id, 
            input_data=input_data,
            retry_count=retry_count,
            max_retries=max_retries,
        )

        result = self._executor.run(
            definition=workflow.definition,
            workflow_id=workflow.id,
            input_data=input_data,
        )

        await self._execution_repo.mark_finished(execution, result)

        return ExecutionResponse(
            workflow_id=workflow.id,
            success=result.success,
            steps_total=result.steps_total,
            steps_executed=result.steps_executed,
            response=result.response,
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

    async def list_executions(
        self, workflow_id: uuid.UUID
    ) -> list[WorkflowExecutionResponse]:
        executions = await self._execution_repo.get_by_workflow_id(workflow_id)
        return [WorkflowExecutionResponse.model_validate(e) for e in executions]

