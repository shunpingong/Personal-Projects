from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    project_name: str = "trust_system"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "replace-this-development-secret-before-production-deployments"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    postgres_server: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "trust_system"
    postgres_user: str = "trust_user"
    postgres_password: str = "trust_password"
    sqlalchemy_echo: bool = False

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    )
    kafka_brokers: list[str] = Field(default_factory=list)
    aws_region: str = "ap-southeast-1"
    aws_s3_bucket: str = "trust-system-artifacts"
    aws_sqs_queue_url: str | None = None
    bootstrap_admin_email: str | None = "admin@trustsystem.local"
    bootstrap_admin_password: str | None = "AdminPassword123!"
    bootstrap_admin_full_name: str = "Trust System Admin"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
