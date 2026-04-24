from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.models.chat import ChatMessage, ChatThread, MessageRole
from app.schemas.chat import (
    ChatMessageRead,
    ChatRequest,
    ChatThreadRead,
    CreateThreadRequest,
    ThreadSummaryRead,
)
from app.modules.rag.graph.builder import RAGGraphService


class ChatService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        graph_service: RAGGraphService | None,
    ):
        self.session = session
        self.graph_service = graph_service
        self.settings = get_settings()

    async def list_threads(self) -> list[ChatThread]:
        result = await self.session.scalars(
            select(ChatThread)
            .options(selectinload(ChatThread.messages))
            .order_by(ChatThread.updated_at.desc())
        )
        return list(result.unique().all())

    async def create_thread(self, payload: CreateThreadRequest) -> ChatThread:
        thread = ChatThread(
            title=(payload.title or "New thread").strip(),
            knowledge_base_id=payload.knowledge_base_id,
        )
        self.session.add(thread)
        await self.session.commit()
        return await self.get_thread(thread.id)

    async def get_thread(self, thread_id: uuid.UUID) -> ChatThread:
        thread = await self.session.scalar(
            select(ChatThread)
            .execution_options(populate_existing=True)
            .options(selectinload(ChatThread.messages))
            .where(ChatThread.id == thread_id)
        )
        if thread is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found.",
            )
        return thread

    async def send_message(self, payload: ChatRequest) -> tuple[ChatThread, ChatMessage]:
        if self.graph_service is None:
            raise RuntimeError("Graph service is required for chat.")

        if payload.thread_id:
            thread = await self.get_thread(payload.thread_id)
        else:
            thread = ChatThread(
                title=self._build_thread_title(payload.message),
                knowledge_base_id=payload.knowledge_base_id,
            )
            self.session.add(thread)
            await self.session.commit()
            thread = await self.get_thread(thread.id)

        if payload.thread_id and payload.knowledge_base_id is not None:
            if thread.knowledge_base_id != payload.knowledge_base_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change the retrieval scope of an existing thread.",
                )

        user_message = ChatMessage(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=payload.message,
        )
        thread.updated_at = datetime.now(timezone.utc)
        self.session.add(user_message)
        await self.session.commit()

        graph_result = await self.graph_service.ask(
            thread_id=str(thread.id),
            message=payload.message,
            knowledge_base_id=str(thread.knowledge_base_id) if thread.knowledge_base_id else None,
            system_prompt=payload.system_prompt,
        )

        assistant_message = ChatMessage(
            thread_id=thread.id,
            role=MessageRole.ASSISTANT,
            content=graph_result.answer,
            sources=graph_result.sources,
            model_name=self.settings.llm_model,
        )
        thread.updated_at = datetime.now(timezone.utc)
        self.session.add(assistant_message)
        await self.session.commit()

        refreshed_thread = await self.get_thread(thread.id)
        await self.session.refresh(assistant_message)
        return refreshed_thread, assistant_message

    def _build_thread_title(self, text: str) -> str:
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            return "New thread"
        return cleaned[:60]


def serialize_thread(thread: ChatThread) -> ChatThreadRead:
    return ChatThreadRead(
        id=thread.id,
        title=thread.title,
        knowledge_base_id=thread.knowledge_base_id,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        messages=[ChatMessageRead.model_validate(message) for message in thread.messages],
    )


def serialize_thread_summary(thread: ChatThread) -> ThreadSummaryRead:
    return ThreadSummaryRead(
        id=thread.id,
        title=thread.title,
        knowledge_base_id=thread.knowledge_base_id,
        message_count=len(thread.messages),
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )
