from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.session import SessionLocal, close_engine
from app.modules.rag.errors import ProviderUnavailableError
from app.modules.rag.graph.builder import RAGGraphService
from app.modules.rag.vector_store import QdrantVectorStoreManager
from app.services.knowledge_service import KnowledgeService


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.uploads_path.mkdir(parents=True, exist_ok=True)

    vector_store = QdrantVectorStoreManager(settings=settings)
    await vector_store.startup()

    async with SessionLocal() as session:
        knowledge_service = KnowledgeService(session=session, vector_store=vector_store)
        try:
            await knowledge_service.sync_all_knowledge_base_routes(ignore_provider_errors=True)
        except ProviderUnavailableError as exc:
            logger.warning("KB routing backfill skipped during startup: %s", exc)

    graph_service = RAGGraphService(settings=settings, vector_store=vector_store)
    await graph_service.startup()

    app.state.vector_store = vector_store
    app.state.graph_service = graph_service

    try:
        yield
    finally:
        await graph_service.shutdown()
        await vector_store.shutdown()
        await close_engine()
