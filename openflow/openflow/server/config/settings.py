"""
Application settings and configuration
"""
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "OpenFlow"
    version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    serverless: bool = False  # Enable serverless mode (Vercel, AWS Lambda, etc.)

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "postgresql+asyncpg://openflow:password@localhost:5432/openflow"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 40
    database_pool_recycle: int = 3600  # Recycle connections after 1 hour
    database_pool_pre_ping: bool = True  # Test connections before using

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.vercel.app",
        "https://*.vercel.com"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # File uploads
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_extensions: list[str] = [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".jpg", ".jpeg", ".png", ".gif", ".svg"
    ]

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"

    @property
    def is_serverless(self) -> bool:
        """Check if running in serverless mode"""
        return self.serverless

    @property
    def should_init_modules(self) -> bool:
        """Check if modules should be initialized at startup"""
        # Skip module initialization in serverless environments
        return not self.serverless

    @property
    def should_init_db(self) -> bool:
        """Check if database should be initialized at startup"""
        # In serverless, use lazy initialization
        return not self.serverless

    def get_db_pool_size(self) -> int:
        """Get appropriate database pool size based on environment"""
        if self.serverless:
            # Serverless: minimal pooling, rely on connection pooler
            return 1
        elif self.is_development:
            # Development: small pool
            return 5
        else:
            # Production: full pool
            return self.database_pool_size

    def get_db_max_overflow(self) -> int:
        """Get appropriate database max overflow based on environment"""
        if self.serverless:
            # Serverless: no overflow
            return 0
        elif self.is_development:
            # Development: small overflow
            return 5
        else:
            # Production: full overflow
            return self.database_max_overflow


# Global settings instance
settings = Settings()
