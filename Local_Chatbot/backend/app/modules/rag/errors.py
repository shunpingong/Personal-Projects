from __future__ import annotations

from typing import NoReturn

from openai import APIConnectionError

from app.core.config import Settings


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class ProviderUnavailableError(RuntimeError):
    """Raised when the configured LLM or embeddings endpoint cannot be reached."""


def raise_provider_unavailable(
    *,
    provider: str,
    settings: Settings,
    exc: APIConnectionError,
) -> NoReturn:
    endpoint = settings.openai_base_url or DEFAULT_OPENAI_BASE_URL

    if settings.openai_base_url and _is_loopback_url(settings.openai_base_url):
        message = (
            f"{provider} endpoint is unreachable from the backend process. "
            "OPENAI_BASE_URL points to localhost, which refers to the backend container itself "
            "under Docker. Use host.docker.internal or a Docker service name instead."
        )
    else:
        message = (
            f"{provider} endpoint is unreachable from the backend process. "
            f"Verify OPENAI_API_KEY, OPENAI_BASE_URL, and outbound access to {endpoint}."
        )

    raise ProviderUnavailableError(message) from exc


def _is_loopback_url(url: str) -> bool:
    lowered = url.lower()
    return "localhost" in lowered or "127.0.0.1" in lowered
