import json
import logging
import uuid

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class QueueService:
    """
    Very simple Redis-backed queue system.
    Uses a Redis List to push and pull jobs asynchronously.
    """

    def __init__(self, redis_client: Redis, queue_name: str = "flowforge:workflow_queue") -> None:
        self._redis = redis_client
        self._queue_name = queue_name

    async def enqueue_workflow(
        self, 
        workflow_id: uuid.UUID, 
        input_data: dict | None = None
    ) -> None:
        """
        Pushes a new workflow job into the tail of the Redis list.
        A background worker can pop these using BLPOP/BRPOP.
        """
        job = {
            "workflow_id": str(workflow_id),
            "input_data": input_data or {}
        }
        
        job_json = json.dumps(job)
        
        # Pushes to the left (head). Workers should BRPOP from the right (tail).
        await self._redis.lpush(self._queue_name, job_json)
        
        logger.info("[queue] Enqueued workflow %s", workflow_id)
