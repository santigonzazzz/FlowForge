import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["My First Workflow"])
    definition: dict = Field(..., examples=[{"steps": []}])
    is_active: bool = Field(default=True)


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    definition: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionStepResult(BaseModel):
    step_index: int
    step_type: str
    success: bool
    output: Any = None
    error: str | None = None


class ExecutionResponse(BaseModel):
    workflow_id: uuid.UUID
    success: bool
    steps_total: int
    steps_executed: int
    response: str | None = None
    results: list[ExecutionStepResult]


class WebhookTriggerResponse(ExecutionResponse):
    payload: dict


class WebhookQueuedResponse(BaseModel):
    status: str = "queued"

    model_config = {"from_attributes": True}


class WorkflowExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    input_data: dict | None = None
    output_data: dict | None = None
    started_at: datetime
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}
