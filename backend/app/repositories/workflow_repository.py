import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate


class WorkflowRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, data: WorkflowCreate) -> Workflow:
        workflow = Workflow(
            name=data.name,
            definition=data.definition,
            is_active=data.is_active,
        )
        self._db.add(workflow)
        await self._db.flush()
        await self._db.refresh(workflow)
        return workflow

    async def get_all(self) -> list[Workflow]:
        result = await self._db.execute(select(Workflow))
        return list(result.scalars().all())

    async def get_by_id(self, workflow_id: uuid.UUID) -> Workflow | None:
        result = await self._db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

