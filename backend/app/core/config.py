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
    OPENALGO_API_URL: str = os.getenv("OPENALGO_API_URL", "http://127.0.0.1:5000/api/v1")
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

    # EXECUTION CONTROL
    EXECUTION_ENABLED: bool = os.getenv("EXECUTION_ENABLED", "false").lower() == "true"
    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "DRY_RUN")  # LIVE, DRY_RUN, DISABLED
    
    # TELEGRAM BOT (Optional - for alerts)
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN", None)
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID", None)
    
    # PILLAR THRESHOLDS - TREND
    TREND_SMA_DAILY_SHORT: int = 50
    TREND_SMA_DAILY_LONG: int = 200
    TREND_SMA_WEEKLY: int = 20
    TREND_SCORE_MAX: float = 60.0
    TREND_BIAS_BULLISH: float = 60.0
    TREND_BIAS_BEARISH: float = 40.0

    # PILLAR THRESHOLDS - MOMENTUM
    MOMENTUM_RSI_BULLISH_MIN: float = 50.0
    MOMENTUM_RSI_BULLISH_MAX: float = 70.0
    MOMENTUM_RSI_OVERBOUGHT: float = 70.0
    MOMENTUM_RSI_OVERSOLD: float = 30.0
    MOMENTUM_RSI_NEUTRAL_MIN: float = 40.0
    MOMENTUM_RSI_NEUTRAL_MAX: float = 50.0
    MOMENTUM_RSI_BIAS_BULLISH: float = 55.0
    MOMENTUM_RSI_BIAS_BEARISH: float = 45.0
    MOMENTUM_SCORE_MAX: float = 40.0

    # PILLAR THRESHOLDS - VOLATILITY
    VOLATILITY_ATR_LOW: float = 1.5
    VOLATILITY_ATR_MODERATE: float = 3.0
    VOLATILITY_ATR_HIGH: float = 5.0
    VOLATILITY_ATR_EXTREME: float = 8.0
    VOLATILITY_BB_WIDTH_VERY_NARROW: float = 4.0
    VOLATILITY_BB_WIDTH_NARROW: float = 8.0
    VOLATILITY_BB_WIDTH_WIDE: float = 12.0
    VOLATILITY_BB_WIDTH_VERY_WIDE: float = 18.0
    VOLATILITY_VIX_VERY_LOW: float = 12.0
    VOLATILITY_VIX_LOW: float = 15.0
    VOLATILITY_VIX_NORMAL: float = 20.0
    VOLATILITY_VIX_ELEVATED: float = 25.0
    VOLATILITY_VIX_HIGH: float = 30.0
    VOLATILITY_WEIGHT_ATR: float = 0.40
    VOLATILITY_WEIGHT_BB: float = 0.30
    VOLATILITY_WEIGHT_VIX: float = 0.30
    VOLATILITY_BIAS_ATR_THRESHOLD: float = 5.0
    VOLATILITY_BIAS_BB_THRESHOLD: float = 12.0
    VOLATILITY_BIAS_VIX_THRESHOLD: float = 25.0

    # PILLAR THRESHOLDS - LIQUIDITY
    LIQUIDITY_SPREAD_EXTREME_TIGHT: float = 0.05
    LIQUIDITY_SPREAD_VERY_TIGHT: float = 0.10
    LIQUIDITY_SPREAD_TIGHT: float = 0.20
    LIQUIDITY_SPREAD_FAIR: float = 0.30
    LIQUIDITY_SPREAD_WIDE: float = 0.50
    LIQUIDITY_DEPTH_RATIO_VERY_BEARISH: float = 0.5
    LIQUIDITY_DEPTH_RATIO_BEARISH: float = 0.7
    LIQUIDITY_DEPTH_RATIO_NEUTRAL_MAX: float = 1.3
    LIQUIDITY_DEPTH_RATIO_BULLISH_MAX: float = 2.0
    LIQUIDITY_ADOSC_VERY_HIGH: float = 2000.0
    LIQUIDITY_ADOSC_HIGH: float = 1000.0
    LIQUIDITY_ADOSC_NEUTRAL: float = 0.0
    LIQUIDITY_ADOSC_LOW: float = -1000.0
    LIQUIDITY_ADOSC_VERY_LOW: float = -2000.0
    LIQUIDITY_WEIGHT_SPREAD_ADOSC: float = 0.50
    LIQUIDITY_WEIGHT_DEPTH_ADOSC: float = 0.30
    LIQUIDITY_WEIGHT_VOLUME_ADOSC: float = 0.20
    LIQUIDITY_WEIGHT_SPREAD_BASE: float = 0.60
    LIQUIDITY_WEIGHT_DEPTH_BASE: float = 0.40
    LIQUIDITY_DEPTH_CRITICAL_THIN: int = 100
    LIQUIDITY_DEPTH_THIN: int = 1000
    LIQUIDITY_BIAS_SPREAD_THRESHOLD: float = 0.30
    LIQUIDITY_BIAS_DEPTH_THRESHOLD: int = 1000
    LIQUIDITY_BIAS_RATIO_THRESHOLD: float = 1.5
    LIQUIDITY_BIAS_ADOSC_THRESHOLD: float = 1000.0

    # PILLAR THRESHOLDS - REGIME
    REGIME_SCORE_BULLISH: float = 85.0
    REGIME_SCORE_BEARISH: float = 15.0
    REGIME_SCORE_NEUTRAL: float = 50.0
    REGIME_VIX_HIGH_THRESHOLD: float = 25.0
    REGIME_VIX_HIGH_ADJUSTMENT: float = -10.0
    REGIME_VIX_LOW_THRESHOLD: float = 15.0
    REGIME_VIX_LOW_ADJUSTMENT: float = 5.0

    # PILLAR THRESHOLDS - SENTIMENT
    SENTIMENT_OI_BUILDUP_BONUS: float = 20.0
    SENTIMENT_OI_COVERING_BONUS: float = 10.0
    SENTIMENT_DELTA_THRESHOLD: float = 0.5
    SENTIMENT_DELTA_BONUS: float = 15.0
    SENTIMENT_GAMMA_RISK_THRESHOLD: float = 0.05
    SENTIMENT_INSIDER_BUY_COUNT_THRESHOLD: int = 3
    SENTIMENT_INSIDER_CLUSTER_BONUS: float = 25.0
    SENTIMENT_INSIDER_NET_VALUE_THRESHOLD: float = 10000000.0
    SENTIMENT_INSIDER_NET_VALUE_BONUS: float = 15.0
    SENTIMENT_INSTITUTIONAL_VOL_PCT: float = 0.05
    SENTIMENT_INSTITUTIONAL_BONUS: float = 20.0
    SENTIMENT_CONVERGENCE_BONUS: float = 15.0
    
    # ========================================================================
    # WEIGHT SCHEDULER - Dynamic Pillar Weighting by Market Regime
    # ========================================================================
    
    # Enable/disable dynamic weight scheduling
    WEIGHT_SCHEDULER_ENABLED: bool = True
    
    # Default weights (used when scheduler disabled or regime unknown)
    WEIGHT_MATRIX_DEFAULT: dict = {
        "trend": 0.30,
        "momentum": 0.20,
        "volatility": 0.10,
        "liquidity": 0.10,
        "sentiment": 0.10,
        "regime": 0.20
    }
    
    # BULLISH regime: Emphasize trend and momentum
    WEIGHT_MATRIX_BULLISH: dict = {
        "trend": 0.35,
        "momentum": 0.25,
        "volatility": 0.05,
        "liquidity": 0.10,
        "sentiment": 0.10,
        "regime": 0.15
    }
    
    # BEARISH regime: Emphasize trend and volatility
    WEIGHT_MATRIX_BEARISH: dict = {
        "trend": 0.35,
        "momentum": 0.15,
        "volatility": 0.20,
        "liquidity": 0.10,
        "sentiment": 0.05,
        "regime": 0.15
    }
    
    # VOLATILE regime: Emphasize volatility and liquidity
    WEIGHT_MATRIX_VOLATILE: dict = {
        "trend": 0.15,
        "momentum": 0.10,
        "volatility": 0.30,
        "liquidity": 0.20,
        "sentiment": 0.10,
        "regime": 0.15
    }
    
    # SIDEWAYS regime: Balanced with sentiment boost
    WEIGHT_MATRIX_SIDEWAYS: dict = {
        "trend": 0.15,
        "momentum": 0.15,
        "volatility": 0.10,
        "liquidity": 0.15,
        "sentiment": 0.25,
        "regime": 0.20
    }
    
    # VIX-based adjustments
    WEIGHT_VIX_LOW_THRESHOLD: float = 15.0  # Below this, reduce volatility weight
    WEIGHT_VIX_HIGH_THRESHOLD: float = 25.0  # Above this, increase volatility weight
    WEIGHT_VIX_ADJUSTMENT_FACTOR: float = 0.05  # How much to adjust

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )

settings = Settings()
