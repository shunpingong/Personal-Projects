from __future__ import annotations

import os

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings


def build_chat_model(settings: Settings) -> BaseChatModel:
    _clear_blank_openai_base_env_vars()
    model_kwargs: dict[str, object] = {
        "temperature": settings.llm_temperature,
    }

    if settings.openai_api_key:
        model_kwargs["api_key"] = settings.openai_api_key
    if settings.openai_base_url:
        model_kwargs["base_url"] = settings.openai_base_url

    return init_chat_model(settings.llm_model, **model_kwargs)


def build_embeddings(settings: Settings) -> OpenAIEmbeddings:
    _clear_blank_openai_base_env_vars()
    model_kwargs: dict[str, object] = {
        "model": settings.embedding_model,
    }

    if settings.openai_api_key:
        model_kwargs["api_key"] = settings.openai_api_key
    if settings.openai_base_url:
        model_kwargs["base_url"] = settings.openai_base_url

    return OpenAIEmbeddings(**model_kwargs)


def _clear_blank_openai_base_env_vars() -> None:
    for env_name in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
        value = os.environ.get(env_name)
        if value is not None and not value.strip():
            os.environ.pop(env_name, None)
