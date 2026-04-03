from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project metadata
    PROJECT_NAME: str = "FlowForge API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Production-ready FastAPI backend"
    API_PREFIX: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Config
    GROQ_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
