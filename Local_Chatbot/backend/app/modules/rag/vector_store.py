from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from openai import APIConnectionError
from qdrant_client import AsyncQdrantClient, models

from app.core.config import Settings
from app.modules.rag.errors import raise_provider_unavailable
from app.modules.rag.providers import build_embeddings


@dataclass(slots=True)
class KnowledgeBaseRoutingRecord:
    knowledge_base_id: str
    name: str
    slug: str
    description: str | None
    routing_summary: str
    document_count: int
    tags: list[str] | None = None
    example_questions: list[str] | None = None


class QdrantVectorStoreManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embeddings = build_embeddings(settings)
        self.client: AsyncQdrantClient | None = None
        self._stores: dict[str, QdrantVectorStore] = {}

    async def startup(self) -> None:
        self.client = AsyncQdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key,
            prefer_grpc=self.settings.qdrant_prefer_grpc,
        )
        await self.ensure_document_collection()
        await self.ensure_routing_collection()

    async def shutdown(self) -> None:
        if self.client and hasattr(self.client, "aclose"):
            await self.client.aclose()

    async def ensure_collection(self) -> None:
        await self.ensure_document_collection()

    async def ensure_document_collection(self) -> None:
        await self._ensure_collection(self.settings.qdrant_collection)

    async def ensure_routing_collection(self) -> None:
        await self._ensure_collection(self.settings.qdrant_routing_collection)

    async def add_documents(self, documents: list[Document]) -> None:
        store = self._get_store(self.settings.qdrant_collection)
        ids = [document.metadata["chunk_id"] for document in documents]
        try:
            await store.aadd_documents(documents=documents, ids=ids)
        except APIConnectionError as exc:
            raise_provider_unavailable(provider="Embeddings", settings=self.settings, exc=exc)

    async def delete_documents(self, ids: list[str]) -> None:
        if not ids:
            return

        client = self._require_client()
        await client.delete(
            collection_name=self.settings.qdrant_collection,
            points_selector=ids,
            wait=True,
        )

    async def upsert_routing_record(self, record: KnowledgeBaseRoutingRecord) -> None:
        store = self._get_store(self.settings.qdrant_routing_collection)
        metadata: dict[str, Any] = {
            "knowledge_base_id": record.knowledge_base_id,
            "knowledge_base_name": record.name,
            "knowledge_base_slug": record.slug,
            "document_count": record.document_count,
        }
        if record.description:
            metadata["knowledge_base_description"] = record.description
        if record.tags:
            metadata["tags"] = record.tags
        if record.example_questions:
            metadata["example_questions"] = record.example_questions

        document = Document(page_content=record.routing_summary, metadata=metadata)
        try:
            await store.aadd_documents(documents=[document], ids=[record.knowledge_base_id])
        except APIConnectionError as exc:
            raise_provider_unavailable(provider="Embeddings", settings=self.settings, exc=exc)

    async def discover_routing_scope(
        self,
        *,
        query: str,
        limit: int,
        score_threshold: float,
        score_margin: float,
    ) -> list[str]:
        store = self._get_store(self.settings.qdrant_routing_collection)
        try:
            results = await store.asimilarity_search_with_relevance_scores(
                query=query,
                k=limit,
                score_threshold=score_threshold,
            )
        except APIConnectionError as exc:
            raise_provider_unavailable(provider="Embeddings", settings=self.settings, exc=exc)

        if not results:
            return []

        strongest_score = float(results[0][1])
        selected_ids: list[str] = []
        for document, score in results:
            knowledge_base_id = document.metadata.get("knowledge_base_id")
            if not knowledge_base_id:
                continue
            if float(score) >= strongest_score - score_margin:
                selected_ids.append(str(knowledge_base_id))

        return selected_ids[:limit]

    async def similarity_search(
        self,
        query: str,
        knowledge_base_ids: list[str] | None,
        limit: int,
        score_threshold: float,
    ) -> list[tuple[Document, float]]:
        store = self._get_store(self.settings.qdrant_collection)
        query_filter = self._build_query_filter(knowledge_base_ids)

        try:
            return await store.asimilarity_search_with_relevance_scores(
                query=query,
                k=limit,
                filter=query_filter,
                score_threshold=score_threshold,
            )
        except APIConnectionError as exc:
            raise_provider_unavailable(provider="Embeddings", settings=self.settings, exc=exc)

    def _get_store(self, collection_name: str) -> QdrantVectorStore:
        store = self._stores.get(collection_name)
        if store is None:
            store = QdrantVectorStore.from_existing_collection(
                collection_name=collection_name,
                embedding=self.embeddings,
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
                prefer_grpc=self.settings.qdrant_prefer_grpc,
                validate_collection_config=False,
            )
            self._stores[collection_name] = store
        return store

    def _require_client(self) -> AsyncQdrantClient:
        if self.client is None:
            raise RuntimeError("Qdrant client has not been initialized.")
        return self.client

    async def _ensure_collection(self, collection_name: str) -> None:
        client = self._require_client()
        exists = await client.collection_exists(collection_name)
        if exists:
            await self._validate_collection(collection_name)
            return

        await client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=self.settings.embedding_dimensions,
                distance=models.Distance.COSINE,
            ),
        )

    def _build_query_filter(
        self,
        knowledge_base_ids: list[str] | None,
    ) -> models.Filter | None:
        if not knowledge_base_ids:
            return None

        if len(knowledge_base_ids) == 1:
            knowledge_base_match: Any = models.MatchValue(value=knowledge_base_ids[0])
        else:
            knowledge_base_match = models.MatchAny(any=knowledge_base_ids)

        return models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.knowledge_base_id",
                    match=knowledge_base_match,
                )
            ]
        )

    async def _validate_collection(self, collection_name: str) -> None:
        client = self._require_client()
        collection = await client.get_collection(collection_name)
        vector_config = collection.config.params.vectors

        if isinstance(vector_config, dict):
            if "" not in vector_config:
                available_vectors = ", ".join(sorted(vector_config.keys())) or "<none>"
                raise RuntimeError(
                    "Existing Qdrant collection uses named vectors that this app is not configured for. "
                    f"Expected the default unnamed vector, found: {available_vectors}."
                )
            dense_vector_config = vector_config[""]
        else:
            dense_vector_config = vector_config

        actual_size = getattr(dense_vector_config, "size", None)
        if actual_size != self.settings.embedding_dimensions:
            raise RuntimeError(
                "Existing Qdrant collection embedding dimensions do not match the backend settings. "
                f"Expected {self.settings.embedding_dimensions}, found {actual_size}."
            )

        actual_distance = getattr(dense_vector_config, "distance", None)
        expected_distance = models.Distance.COSINE
        if actual_distance != expected_distance:
            raise RuntimeError(
                "Existing Qdrant collection distance metric does not match the backend settings. "
                f"Expected {expected_distance}, found {actual_distance}."
            )
