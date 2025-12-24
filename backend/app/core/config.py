import os
from typing import List, Union, Any, Optional
from pydantic import AnyHttpUrl, validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fortune Trading QUAD"
    API_V1_STR: str = "/api/v1"
    
    # CORS - Allow localhost for development
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3006",  # Added for Next.js frontend
        "http://localhost:3010",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3006",
        "http://127.0.0.1:3010"
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    # Fallback to simple split if JSON load fails
                    return [i.strip().strip('"').strip("'") for i in v[1:-1].split(",")]
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    # DATABASE
    # When running in Docker, use 'db' as server. 
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "quad_trading"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"

    # REDIS
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URI: Optional[str] = None

    @validator("REDIS_URI", pre=True)
    def assemble_redis_uri(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    # OPENALGO
    OPENALGO_WS_URL: str = "ws://127.0.0.1:8765"
    OPENALGO_API_URL: str = os.getenv("OPENALGO_API_URL", "http://127.0.0.1:8765/api")
    OPENALGO_API_KEY: str = os.getenv("OPENALGO_API_KEY", "default_key")
    OPENALGO_RECONNECT_ATTEMPTS: int = 10
    OPENALGO_HEARTBEAT_INTERVAL: int = 30  # seconds
    OPENALGO_MAX_SYMBOLS_PER_CONN: int = 500
    REDIS_TICK_TTL: int = 5  # seconds

    # EXECUTION SAFETY
    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "DRY_RUN") # "DRY_RUN" or "LIVE"
    EXECUTION_ENABLED: bool = os.getenv("EXECUTION_ENABLED", "false").lower() == "true"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
