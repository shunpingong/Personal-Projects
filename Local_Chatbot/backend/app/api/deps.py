from __future__ import annotations

from fastapi import Request

from app.modules.rag.graph.builder import RAGGraphService
from app.modules.rag.vector_store import QdrantVectorStoreManager


def get_graph_service(request: Request) -> RAGGraphService:
    return request.app.state.graph_service


def get_vector_store_manager(request: Request) -> QdrantVectorStoreManager:
    return request.app.state.vector_store

