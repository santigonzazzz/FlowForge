from fastapi import APIRouter

from app.routes.health import router as health_router
from app.routes.webhooks import router as webhooks_router
from app.routes.workflows import router as workflows_router

router = APIRouter()

router.include_router(health_router, prefix="/health")
router.include_router(workflows_router, prefix="/workflows", tags=["Workflows"])
router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])

# Add more domain routers below as you create them.
# Example:
# from app.routes.users import router as users_router
# router.include_router(users_router, prefix="/users", tags=["Users"])
