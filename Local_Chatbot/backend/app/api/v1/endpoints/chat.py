from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_graph_service
from app.db.session import get_session
from app.modules.rag.errors import ProviderUnavailableError
from app.modules.rag.graph.builder import RAGGraphService
from app.schemas.chat import (
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
    ChatThreadRead,
    CreateThreadRequest,
    ThreadSummaryRead,
)
from app.services.chat_service import ChatService, serialize_thread, serialize_thread_summary


router = APIRouter(tags=["chat"])


@router.get("/threads", response_model=list[ThreadSummaryRead])
async def list_threads(
    session: AsyncSession = Depends(get_session),
) -> list[ThreadSummaryRead]:
    service = ChatService(session=session, graph_service=None)
    threads = await service.list_threads()
    return [serialize_thread_summary(thread) for thread in threads]


@router.post("/threads", response_model=ChatThreadRead)
async def create_thread(
    payload: CreateThreadRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatThreadRead:
    service = ChatService(session=session, graph_service=None)
    thread = await service.create_thread(payload)
    return serialize_thread(thread)


@router.get("/threads/{thread_id}", response_model=ChatThreadRead)
async def get_thread(
    thread_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ChatThreadRead:
    service = ChatService(session=session, graph_service=None)
    thread = await service.get_thread(thread_id)
    return serialize_thread(thread)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session),
    graph_service: RAGGraphService = Depends(get_graph_service),
) -> ChatResponse:
    service = ChatService(session=session, graph_service=graph_service)
    try:
        thread, assistant_message = await service.send_message(payload)
    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return ChatResponse(
        thread=serialize_thread(thread),
        assistant_message=ChatMessageRead.model_validate(assistant_message),
    )
