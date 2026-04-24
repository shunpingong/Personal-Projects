from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Local Chatbot API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/local_chatbot"
    langgraph_database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/local_chatbot?sslmode=disable"
    )

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "local_chatbot_documents"
    qdrant_routing_collection: str = "local_chatbot_kb_routes"
    qdrant_prefer_grpc: bool = False

    uploads_dir: Path = Field(default=Path("storage/uploads"))
    rag_top_k: int = 5
    rag_score_threshold: float = 0.25
    rag_chunk_size: int = 900
    rag_chunk_overlap: int = 150
    kb_routing_top_k: int = 3
    kb_routing_score_threshold: float = 0.2
    kb_routing_score_margin: float = 0.08
    kb_routing_max_document_previews: int = 4
    kb_routing_preview_chars: int = 320

    llm_model: str = "openai:gpt-4.1-mini"
    llm_temperature: float = 0.2
    openai_api_key: str | None = None
    openai_base_url: str | None = None

    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    default_system_prompt: str = (
        "You are a grounded RAG assistant. Use retrieved knowledge when available, "
        "be explicit when the evidence is incomplete, and keep answers concise and useful."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def uploads_path(self) -> Path:
        path = Path(self.uploads_dir)
        return path if path.is_absolute() else BASE_DIR / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
