import asyncio
import json
import logging
import sys
import uuid

import redis.asyncio as redis

from app.core.redis import redis_pool
from app.db.session import AsyncSessionLocal
from app.services.workflow_service import WorkflowService

# Configurar logs básicos si el script se llama de forma independiente
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("workflow_worker")

QUEUE_NAME = "flowforge:workflow_queue"


async def process_job(job_json: str, rc: redis.Redis) -> None:
    """Intenta decodificar de JSON y ejecutar el workflow mediante WorkflowService."""
    try:
        job = json.loads(job_json)
        workflow_id_str = job.get("workflow_id")
        input_data = job.get("input_data", {})
        retry_count = job.get("retry_count", 0)
        max_retries = job.get("max_retries", 3)

        if not workflow_id_str:
            logger.error("Invalid job: missing workflow_id. Data: %s", job_json)
            return

        workflow_id = uuid.UUID(workflow_id_str)
        logger.info("Processing job for workflow_id=%s (Retry: %d/%d)", workflow_id, retry_count, max_retries)

        # Crear transaccion local con la DB para este job
        async with AsyncSessionLocal() as db:
            service = WorkflowService(db)
            
            # Reutiliza el WorkflowService que ya inserta ejecuciones en BD
            result = await service.execute_workflow(
                workflow_id, 
                input_data=input_data, 
                retry_count=retry_count, 
                max_retries=max_retries
            )
            
            is_success = result.success
            
            if not is_success:
                if retry_count < max_retries:
                    retry_count += 1
                    logger.warning(
                        "Workflow_id=%s failed. Delaying 2s and Re-queueing (%d/%d)...", 
                        workflow_id, retry_count, max_retries
                    )
                    await asyncio.sleep(2)
                    
                    job["retry_count"] = retry_count
                    job["max_retries"] = max_retries
                    # Se inserta en LRU para que los workers lo levanten apenas terminen.
                    await rc.lpush(QUEUE_NAME, json.dumps(job))
                else:
                    logger.error("Workflow_id=%s severely failed and reached max_retries (%d). Marking as permanent failure.", workflow_id, max_retries)
            else:
                logger.info(
                    "Completed workflow_id=%s | Status=SUCCESS | Steps=%d/%d",
                    workflow_id, result.steps_executed, result.steps_total
                )

    except json.JSONDecodeError:
        logger.error("Failed to decode job JSON: %s", job_json)
    except Exception as e:
        logger.exception("Unexpected error processing job: %s", job_json)


async def worker_loop() -> None:
    """Loop infinito que bloquea de forma asíncrona esperando jobs en Redis."""
    rc = redis.Redis(connection_pool=redis_pool)
    logger.info("Worker started. Listening continuously on queue '%s'...", QUEUE_NAME)

    try:
        while True:
            try:
                # BRPOP detiene el loop eternamente (timeout=0) hasta tener elementos.
                # Devuelve una tupla (lista_str, elemento)
                result = await rc.brpop(QUEUE_NAME, timeout=0)
                if not result:
                    continue
                
                _, item_json = result
                
                # Procesar trabajo secuencial.
                # En un sistema grande esto podría lanzarse como tarea separada con asyncio.create_task()
                await process_job(item_json, rc)

            except redis.ConnectionError as e:
                logger.error("Redis Connection Error: %s. Retrying in 5 seconds...", e)
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info("Worker loop cancelled.")
                break
            except Exception:
                logger.exception("Fatal error in worker loop. Continuing anyway.")
                await asyncio.sleep(5)
    finally:
        await rc.aclose()


if __name__ == "__main__":
    # Workaround nativo para errores de asyncio de Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker terminated gracefully by user (Ctrl+C).")
