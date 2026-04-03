import uuid

from typing import Union

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.redis import get_redis_client
from app.db.session import get_db
from app.schemas.workflow import WebhookTriggerResponse, WebhookQueuedResponse
from app.services.webhook_service import WebhookService
from app.services.queue_service import QueueService

router = APIRouter()


def get_webhook_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> WebhookService:
    return WebhookService(db, QueueService(redis))


@router.post(
    "/{workflow_id}",
    response_model=Union[WebhookQueuedResponse, WebhookTriggerResponse],
    status_code=status.HTTP_200_OK,
    summary="Trigger a workflow via webhook",
    description=(
        "Receives an arbitrary JSON payload and executes the matching workflow. "
        "The workflow's `definition.trigger.type` must equal `'webhook'`."
    ),
    responses={
        404: {"description": "Workflow not found"},
        409: {"description": "Workflow is inactive"},
        422: {"description": "Workflow does not have a webhook trigger"},
    },
)
async def trigger_webhook(
    workflow_id: uuid.UUID,
    payload: dict,
    sync: bool = False,
    service: WebhookService = Depends(get_webhook_service),
) -> Union[WebhookQueuedResponse, WebhookTriggerResponse]:
    if sync:
        return await service.trigger(workflow_id=workflow_id, payload=payload)
    return await service.trigger_async(workflow_id=workflow_id, payload=payload)
