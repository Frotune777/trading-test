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

    # PostgreSQL settings (Primary Database)
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "quad_trading")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        
        # Use PostgreSQL for all environments
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

    # ANGEL ONE BROKER
    ANGELONE_API_KEY: str = os.getenv("ANGELONE_API_KEY", "")
    ANGELONE_CLIENT_ID: str = os.getenv("ANGELONE_CLIENT_ID", "")
    ANGELONE_PASSWORD: str = os.getenv("ANGELONE_PASSWORD", "")
    ANGELONE_TOTP_SECRET: str = os.getenv("ANGELONE_TOTP_SECRET", "")
    ANGELONE_WS_URL: str = "ws://smartapisocket.angelone.in/smart-stream"
    ANGELONE_REST_URL: str = "https://apiconnect.angelone.in"
    
    # BROKER SELECTION
    PRIMARY_BROKER: str = os.getenv("PRIMARY_BROKER", "angelone")  # "angelone" or "openalgo"

    # SECURITY (OpenAlgo-inspired)
    API_KEY_PEPPER: str = os.getenv("API_KEY_PEPPER", "")
    SESSION_EXPIRY_TIME: str = os.getenv("SESSION_EXPIRY_TIME", "03:00")  # IST time for cache expiry

    @validator("API_KEY_PEPPER")
    def validate_pepper(cls, v: str) -> str:
        """Validate that API_KEY_PEPPER is set and sufficiently long"""
        if not v:
            raise ValueError(
                "API_KEY_PEPPER environment variable is required. "
                "Generate one using: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if len(v) < 32:
            raise ValueError(
                f"API_KEY_PEPPER must be at least 32 characters (got {len(v)}). "
                "Generate a secure pepper using: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    # EXECUTION SAFETY
    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "DRY_RUN") # "DRY_RUN" or "LIVE"
    EXECUTION_ENABLED: bool = os.getenv("EXECUTION_ENABLED", "false").lower() == "true"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
