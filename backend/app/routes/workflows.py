import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.workflow import (
    ExecutionResponse,
    WorkflowCreate,
    WorkflowExecutionResponse,
    WorkflowResponse,
)
from app.services.workflow_service import WorkflowService

router = APIRouter()


def get_workflow_service(db: AsyncSession = Depends(get_db)) -> WorkflowService:
    return WorkflowService(db)


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow",
)
async def create_workflow(
    payload: WorkflowCreate,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    return await service.create_workflow(payload)


@router.get(
    "",
    response_model=list[WorkflowResponse],
    status_code=status.HTTP_200_OK,
    summary="List all workflows",
)
async def list_workflows(
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowResponse]:
    return await service.list_workflows()


@router.post(
    "/{workflow_id}/execute",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a workflow by ID",
    responses={
        404: {"description": "Workflow not found"},
        409: {"description": "Workflow is inactive"},
    },
)
async def execute_workflow(
    workflow_id: uuid.UUID,
    service: WorkflowService = Depends(get_workflow_service),
) -> ExecutionResponse:
    return await service.execute_workflow(workflow_id)


@router.get(
    "/{workflow_id}/executions",
    response_model=list[WorkflowExecutionResponse],
    status_code=status.HTTP_200_OK,
    summary="List workflow executions",
    description="Gets all executions for a given workflow, ordered by the start date in descending order",
)
async def list_workflow_executions(
    workflow_id: uuid.UUID,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowExecutionResponse]:
    return await service.list_executions(workflow_id)

