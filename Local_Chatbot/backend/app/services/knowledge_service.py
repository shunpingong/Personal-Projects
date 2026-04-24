from __future__ import annotations

import asyncio
import logging
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import BASE_DIR, get_settings
from app.db.models.knowledge import DocumentStatus, KnowledgeBase, SourceDocument
from app.modules.rag.errors import ProviderUnavailableError
from app.modules.rag.loaders import extract_text, load_upload
from app.modules.rag.vector_store import KnowledgeBaseRoutingRecord, QdrantVectorStoreManager
from app.schemas.knowledge import KnowledgeBaseCreate


logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        vector_store: QdrantVectorStoreManager | None,
    ):
        self.session = session
        self.vector_store = vector_store
        self.settings = get_settings()

    async def list_knowledge_bases(self) -> list[KnowledgeBase]:
        result = await self.session.scalars(
            select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
        )
        return list(result.all())

    async def create_knowledge_base(self, payload: KnowledgeBaseCreate) -> KnowledgeBase:
        slug = await self._generate_unique_slug(payload.name)
        knowledge_base = KnowledgeBase(
            name=payload.name.strip(),
            description=self._clean_optional_text(payload.description),
            slug=slug,
        )
        self.session.add(knowledge_base)

        try:
            await self.session.flush()
            if self.vector_store is not None:
                await self._sync_knowledge_base_route(knowledge_base)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        await self.session.refresh(knowledge_base)
        return knowledge_base

    async def list_documents(self, knowledge_base_id: uuid.UUID) -> list[SourceDocument]:
        await self._get_knowledge_base(knowledge_base_id)
        result = await self.session.scalars(
            select(SourceDocument)
            .where(SourceDocument.knowledge_base_id == knowledge_base_id)
            .order_by(SourceDocument.created_at.desc())
        )
        return list(result.all())

    async def ingest_document(
        self,
        *,
        knowledge_base_id: uuid.UUID,
        upload: UploadFile,
    ) -> SourceDocument:
        if self.vector_store is None:
            raise RuntimeError("Vector store is required for ingestion.")

        knowledge_base = await self._get_knowledge_base(knowledge_base_id)
        artifact = await load_upload(upload)
        routing_preview = self._build_routing_preview(artifact.text)

        target_dir = self.settings.uploads_path / str(knowledge_base.id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{artifact.checksum}_{artifact.filename}"
        await asyncio.to_thread(target_file.write_bytes, artifact.raw_bytes)

        source_document = SourceDocument(
            knowledge_base_id=knowledge_base.id,
            filename=artifact.filename,
            content_type=artifact.content_type,
            checksum=artifact.checksum,
            storage_path=str(target_file.relative_to(BASE_DIR)),
            routing_preview=routing_preview,
            status=DocumentStatus.PROCESSING,
        )
        self.session.add(source_document)
        await self.session.commit()
        await self.session.refresh(source_document)

        prepared_chunks: list[Document] = []
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.settings.rag_chunk_size,
                chunk_overlap=self.settings.rag_chunk_overlap,
            )
            chunks = splitter.create_documents(
                texts=[artifact.text],
                metadatas=[
                    {
                        "knowledge_base_id": str(knowledge_base.id),
                        "knowledge_base_name": knowledge_base.name,
                        "source_document_id": str(source_document.id),
                        "filename": artifact.filename,
                    }
                ],
            )
            prepared_chunks = self._prepare_chunks(chunks)

            await self.vector_store.ensure_document_collection()
            await self.vector_store.add_documents(prepared_chunks)

            refreshed_document = await self.session.get(SourceDocument, source_document.id)
            if refreshed_document is None:
                raise RuntimeError("Source document disappeared during ingestion.")

            refreshed_document.chunk_count = len(prepared_chunks)
            refreshed_document.status = DocumentStatus.READY
            refreshed_document.error_message = None
            refreshed_document.routing_preview = routing_preview
            await self.session.flush()
            await self._sync_knowledge_base_route(knowledge_base)
            await self.session.commit()
            await self.session.refresh(refreshed_document)
            return refreshed_document
        except Exception as exc:
            await self.session.rollback()
            if prepared_chunks:
                chunk_ids = [str(chunk.metadata["chunk_id"]) for chunk in prepared_chunks]
                try:
                    await self.vector_store.delete_documents(chunk_ids)
                except Exception as cleanup_exc:
                    logger.warning("Failed to clean up chunk vectors after ingestion error: %s", cleanup_exc)

            failed_document = await self.session.get(SourceDocument, source_document.id)
            if failed_document is not None:
                failed_document.status = DocumentStatus.FAILED
                failed_document.error_message = str(exc)
                failed_document.chunk_count = 0
                await self.session.commit()
            raise

    async def sync_all_knowledge_base_routes(
        self,
        *,
        ignore_provider_errors: bool = False,
    ) -> None:
        if self.vector_store is None:
            raise RuntimeError("Vector store is required for KB routing sync.")

        knowledge_bases = await self.list_knowledge_bases()
        for knowledge_base in knowledge_bases:
            try:
                await self._backfill_missing_routing_previews(knowledge_base.id)
                await self.session.commit()
                await self._sync_knowledge_base_route(knowledge_base)
            except ProviderUnavailableError as exc:
                await self.session.rollback()
                if ignore_provider_errors:
                    logger.warning("Skipping KB routing sync during startup: %s", exc)
                    return
                raise
            except Exception:
                await self.session.rollback()
                raise

    def _prepare_chunks(self, chunks: list[Document]) -> list[Document]:
        prepared: list[Document] = []
        for index, chunk in enumerate(chunks):
            metadata = dict(chunk.metadata)
            source_document_id = uuid.UUID(str(metadata["source_document_id"]))
            metadata["chunk_id"] = str(uuid.uuid5(source_document_id, f"chunk-{index}"))
            metadata["chunk_index"] = index
            prepared.append(Document(page_content=chunk.page_content, metadata=metadata))
        return prepared

    async def _sync_knowledge_base_route(self, knowledge_base: KnowledgeBase) -> None:
        if self.vector_store is None:
            return

        await self._backfill_missing_routing_previews(knowledge_base.id)
        record = await self._build_routing_record(knowledge_base)
        await self.vector_store.ensure_routing_collection()
        await self.vector_store.upsert_routing_record(record)

    async def _build_routing_record(
        self,
        knowledge_base: KnowledgeBase,
    ) -> KnowledgeBaseRoutingRecord:
        ready_documents = await self._list_ready_documents(knowledge_base.id)
        preview_limit = max(1, self.settings.kb_routing_max_document_previews)
        preview_documents = ready_documents[:preview_limit]

        summary_parts = [
            f"Knowledge base name: {knowledge_base.name}",
            f"Knowledge base slug: {knowledge_base.slug}",
        ]
        if knowledge_base.description:
            summary_parts.append(f"Knowledge base description: {knowledge_base.description}")

        if ready_documents:
            summary_parts.append(f"Indexed document count: {len(ready_documents)}")
            summary_parts.append(
                "Document filenames: "
                + ", ".join(document.filename for document in preview_documents)
            )
            for document in preview_documents:
                if document.routing_preview:
                    summary_parts.append(f"{document.filename}: {document.routing_preview}")
        else:
            summary_parts.append("No indexed documents are available yet.")

        return KnowledgeBaseRoutingRecord(
            knowledge_base_id=str(knowledge_base.id),
            name=knowledge_base.name,
            slug=knowledge_base.slug,
            description=knowledge_base.description,
            routing_summary="\n".join(summary_parts),
            document_count=len(ready_documents),
            tags=[token for token in knowledge_base.slug.split("-") if token] or None,
        )

    async def _list_ready_documents(self, knowledge_base_id: uuid.UUID) -> list[SourceDocument]:
        result = await self.session.scalars(
            select(SourceDocument)
            .where(SourceDocument.knowledge_base_id == knowledge_base_id)
            .where(SourceDocument.status == DocumentStatus.READY)
            .order_by(SourceDocument.created_at.desc())
        )
        return list(result.all())

    async def _backfill_missing_routing_previews(self, knowledge_base_id: uuid.UUID) -> None:
        result = await self.session.scalars(
            select(SourceDocument)
            .where(SourceDocument.knowledge_base_id == knowledge_base_id)
            .where(SourceDocument.status == DocumentStatus.READY)
            .where(SourceDocument.routing_preview.is_(None))
        )
        missing_previews = list(result.all())

        for document in missing_previews:
            preview = await self._load_routing_preview_from_storage(document)
            if preview:
                document.routing_preview = preview

    async def _load_routing_preview_from_storage(
        self,
        document: SourceDocument,
    ) -> str | None:
        stored_path = BASE_DIR / document.storage_path
        if not stored_path.exists():
            logger.warning("Stored upload is missing for routing preview backfill: %s", stored_path)
            return None

        suffix = Path(document.filename).suffix.lower()
        try:
            raw_bytes = await asyncio.to_thread(stored_path.read_bytes)
            text = await asyncio.to_thread(extract_text, raw_bytes, suffix)
        except Exception as exc:
            logger.warning("Failed to rebuild routing preview for %s: %s", document.filename, exc)
            return None

        return self._build_routing_preview(text)

    def _build_routing_preview(self, text: str) -> str | None:
        compact_text = re.sub(r"\s+", " ", text).strip()
        if not compact_text:
            return None

        preview_chars = max(80, self.settings.kb_routing_preview_chars)
        return compact_text[:preview_chars]

    async def _get_knowledge_base(self, knowledge_base_id: uuid.UUID) -> KnowledgeBase:
        knowledge_base = await self.session.get(KnowledgeBase, knowledge_base_id)
        if knowledge_base is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found.",
            )
        return knowledge_base

    async def _generate_unique_slug(self, raw_name: str) -> str:
        base_slug = re.sub(r"[^a-z0-9]+", "-", raw_name.strip().lower()).strip("-") or "knowledge-base"
        candidate = base_slug
        suffix = 2

        while True:
            existing = await self.session.scalar(
                select(KnowledgeBase).where(KnowledgeBase.slug == candidate)
            )
            if existing is None:
                return candidate
            candidate = f"{base_slug}-{suffix}"
            suffix += 1

    def _clean_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None
