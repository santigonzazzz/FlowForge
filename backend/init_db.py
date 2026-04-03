import asyncio
from app.db.base import Base
from app.db.session import engine

# Import all models to ensure they are registered with Base metadata
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution

async def init_models():
    async with engine.begin() as conn:
        print("Conectando a Neon Postgres...")
        await conn.run_sync(Base.metadata.create_all)
    print("Migraciones ejecutadas: Tablas de FlowForge generadas correctamente!")

if __name__ == "__main__":
    asyncio.run(init_models())
