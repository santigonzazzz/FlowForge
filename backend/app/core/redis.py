import logging
from typing import AsyncGenerator

import redis.asyncio as redis
from fastapi import Request

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configurar el pool de conexiones usando el URL definido en las settings
# decode_responses=True hace que Redis retorne strings de Python en lugar de bytes
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL, 
    decode_responses=True
)


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    FastAPI dependency inyectable que provee un cliente Redis.
    Usa un connection pool global y se encarga de cerrar la conexión al finalizar.
    """
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()


async def close_redis_connection() -> None:
    """
    Cierra por completo el connection pool global.
    Ideal para llamar en el evento "shutdown" de FastAPI.
    """
    await redis_pool.disconnect()
