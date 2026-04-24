from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_vector_store_manager
from app.db.session import get_session
from app.modules.rag.errors import ProviderUnavailableError
from app.modules.rag.vector_store import QdrantVectorStoreManager
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseRead, SourceDocumentRead
from app.services.knowledge_service import KnowledgeService


router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseRead])
async def list_knowledge_bases(
    session: AsyncSession = Depends(get_session),
) -> list[KnowledgeBaseRead]:
    service = KnowledgeService(session=session, vector_store=None)
    knowledge_bases = await service.list_knowledge_bases()
    return [KnowledgeBaseRead.model_validate(item) for item in knowledge_bases]


@router.post("", response_model=KnowledgeBaseRead)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    session: AsyncSession = Depends(get_session),
    vector_store: QdrantVectorStoreManager = Depends(get_vector_store_manager),
) -> KnowledgeBaseRead:
    service = KnowledgeService(session=session, vector_store=vector_store)
    try:
        knowledge_base = await service.create_knowledge_base(payload)
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return KnowledgeBaseRead.model_validate(knowledge_base)


@router.get("/{knowledge_base_id}/documents", response_model=list[SourceDocumentRead])
async def list_documents(
    knowledge_base_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[SourceDocumentRead]:
    service = KnowledgeService(session=session, vector_store=None)
    documents = await service.list_documents(knowledge_base_id)
    return [SourceDocumentRead.model_validate(item) for item in documents]


@router.post("/{knowledge_base_id}/documents", response_model=SourceDocumentRead)
async def upload_document(
    knowledge_base_id: uuid.UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    vector_store: QdrantVectorStoreManager = Depends(get_vector_store_manager),
) -> SourceDocumentRead:
    service = KnowledgeService(session=session, vector_store=vector_store)
    try:
        document = await service.ingest_document(knowledge_base_id=knowledge_base_id, upload=file)
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return SourceDocumentRead.model_validate(document)
