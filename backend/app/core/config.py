from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and optional .env file.
    Production deployments must set SECRET_KEY and DATABASE_URL; do not rely on defaults.
    """

    database_url: str = Field(
        default="sqlite:///./dev.db",
        description="SQLAlchemy database URL (DATABASE_URL).",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching (REDIS_URL).",
    )
    secret_key: str = Field(
        default="",
        description="JWT signing secret (SECRET_KEY). Required for token issuance.",
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated browser origins allowed for CORS (CORS_ORIGINS).",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
