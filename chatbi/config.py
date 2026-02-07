import logging
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field, model_validator

"""Initialize configuration with environment variables."""
dotenv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=dotenv_file)
# Disable uvicorn error logging to avoid duplicate logs
logging.getLogger("uvicorn.error").disabled = True

# Logger configuration
logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<yellow>[{extra[request_id]}]</yellow> | "
    "<level>{level: <8}</level> | "
    "<cyan>{module}.{function}:{line}</cyan> - <level>{message}</level>"
)

default_request_id = "INIT"


class EnvironmentType(str, Enum):
    """Environment types for application configuration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class LogConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = logger_format
    diagnose: bool = False
    backtrace: bool = False
    log_file: str = "runs/run.log"
    rotation: str = "1 week"
    retention: str = "1 month"
    error_log: str = "runs/logs/error_{time:YYYY-MM-DD}.log"


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: str = field(default_factory=lambda: os.getenv("DB_PORT", "15432"))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", "chatbi"))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "chatbi"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "12345"))
    pool_min: int = field(default_factory=lambda: int(os.getenv("DB_POOL_MIN", "5")))
    pool_max: int = field(default_factory=lambda: int(os.getenv("DB_POOL_MAX", "20")))
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5")))
    max_overflow: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "10"))
    )
    pool_timeout: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT", "30"))
    )
    pool_recycle: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_RECYCLE", "1800"))
    )

    @property
    def connection_url(self) -> str:
        """Get the database connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class CacheConfig:
    """Cache configuration settings."""

    type: str = field(default_factory=lambda: os.getenv("CACHE_TYPE", "memory"))
    url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    ttl: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL", "3600")))


@dataclass
class LLMConfig:
    """LLM service configuration."""

    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai"))
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-3.5-turbo"))
    temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.7"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "4000"))
    )
    timeout: int = field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "60")))


@dataclass
class JWTConfig:
    """JWT authentication configuration."""

    secret_key: str = field(
        default_factory=lambda: os.getenv(
            "JWT_SECRET_KEY",
            "chatbi-dev-secret-key-change-in-production-please",  # 默认开发密钥
        )
    )
    algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = field(
        default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    )
    refresh_token_expire_days: int = field(
        default_factory=lambda: int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    )


@dataclass
class APIConfig:
    """API configuration settings."""

    allow_origins: list[str] = field(
        default_factory=lambda: os.getenv(
            "ALLOW_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
    )
    require_auth: bool = field(
        default_factory=lambda: os.getenv("REQUIRE_AUTH", "False").lower()
        in ("true", "1", "t")
    )
    rate_limit: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT", "100")))
    rate_limit_window: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
    )


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration."""

    host: str = field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
    grpc_port: int = field(default_factory=lambda: int(os.getenv("QDRANT_GRPC_PORT", "6334")))
    prefer_grpc: bool = field(
        default_factory=lambda: os.getenv("QDRANT_PREFER_GRPC", "True").lower()
        in ("true", "1", "t")
    )
    collection_name: str = field(
        default_factory=lambda: os.getenv("QDRANT_COLLECTION_NAME", "chatbi_mdl")
    )
    vector_size: int = field(
        default_factory=lambda: int(os.getenv("QDRANT_VECTOR_SIZE", "1536"))
    )


@dataclass
class LangfuseConfig:
    """Langfuse observability configuration."""

    enabled: bool = field(
        default_factory=lambda: os.getenv("LANGFUSE_ENABLED", "False").lower()
        in ("true", "1", "t")
    )
    public_key: str = field(default_factory=lambda: os.getenv("LANGFUSE_PUBLIC_KEY", ""))
    secret_key: str = field(default_factory=lambda: os.getenv("LANGFUSE_SECRET_KEY", ""))
    host: str = field(
        default_factory=lambda: os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )
    sample_rate: float = field(
        default_factory=lambda: float(os.getenv("LANGFUSE_SAMPLE_RATE", "1.0"))
    )  # 采样率，1.0 表示全量追踪
    flush_interval: int = field(
        default_factory=lambda: int(os.getenv("LANGFUSE_FLUSH_INTERVAL", "10"))
    )  # 上报间隔（秒）
    debug: bool = field(
        default_factory=lambda: os.getenv("LANGFUSE_DEBUG", "False").lower()
        in ("true", "1", "t")
    )


class Config:
    """Application configuration class."""

    def __init__(self):
        # Core settings
        self.env: str = os.getenv("ENV", "development")
        self.debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
        self.diagnose: bool = False
        self.app_name: str = "SmartBI"
        self.version: str = "0.1.0"

        # Component configurations
        self.log = LogConfig()
        self.database = DatabaseConfig()
        self.cache_type = os.getenv("CACHE_TYPE", "memory")
        self.cache = CacheConfig()
        self.llm = LLMConfig()
        self.jwt = JWTConfig()
        self.api = APIConfig()
        self.qdrant = QdrantConfig()
        self.langfuse = LangfuseConfig()

        # Initialize logger
        self.init_logger()

    def init_logger(self):
        """Initialize logger with configured settings."""
        logger.configure(extra={"request_id": default_request_id})
        logger.remove()

        # Console logger
        logger.add(
            sys.stderr,
            format=self.log.format,
            backtrace=self.log.backtrace,
            diagnose=self.log.diagnose,
            enqueue=False,
            level=self.log.level,
        )

        # File logger for all logs
        logger.add(
            self.log.log_file,
            format=self.log.format,
            backtrace=self.log.backtrace,
            diagnose=self.log.diagnose,
            enqueue=True,
            rotation=self.log.rotation,
            retention=self.log.retention,
            level="DEBUG",
        )

        # Separate error file logger
        logger.add(
            self.log.error_log,
            format=self.log.format,
            backtrace=True,
            diagnose=True,
            enqueue=True,
            level="ERROR",
            rotation=self.log.rotation,
            retention=self.log.retention,
        )

    def logger_diagnose(self):
        """Configure logger with diagnostics enabled for debugging."""
        logger.configure(extra={"request_id": default_request_id})
        logger.remove()
        logger.add(
            sys.stderr,
            format=self.log.format,
            backtrace=True,
            diagnose=True,
            enqueue=True,
            level="DEBUG",
        )

    def update(self, diagnose: bool = False):
        """Update configuration settings."""
        self.diagnose = diagnose
        if diagnose:
            self.logger_diagnose()
        else:
            self.init_logger()

    def to_json(self) -> dict[str, Any]:
        """Convert configuration to JSON-serializable dict."""
        return {
            "env": self.env,
            "debug": self.debug,
            "diagnose": self.diagnose,
            "app_name": self.app_name,
            "version": self.version,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
                "user": self.database.user,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
            },
            "cache": {
                "type": self.cache.type,
                "ttl": self.cache.ttl,
            },
            "api": {
                "allow_origins": self.api.allow_origins,
                "require_auth": self.api.require_auth,
                "rate_limit": self.api.rate_limit,
            },
        }


# Create a singleton config instance
config = Config()


@lru_cache
def get_config() -> Config:
    """Get the application configuration (cached)."""
    return config


# Pydantic model for config updates via API
class ConfigModel(BaseModel):
    """Pydantic model for configuration updates via API."""

    diagnose: Optional[bool] = Field(None, description="Enable diagnostic logging")
    debug: Optional[bool] = Field(None, description="Enable debug mode")

    @model_validator(mode="before")
    @classmethod
    def validate_config(cls, data):
        """Validate that at least one field is provided."""
        if isinstance(data, dict) and not any(data.values()):
            raise ValueError("At least one configuration parameter must be provided")
        return data
