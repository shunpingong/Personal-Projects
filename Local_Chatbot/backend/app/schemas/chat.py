from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.chat import MessageRole


class SourceAttribution(BaseModel):
    document_id: str
    filename: str
    snippet: str
    score: float
    knowledge_base_id: str | None = None
    knowledge_base_name: str | None = None


class CreateThreadRequest(BaseModel):
    title: str | None = None
    knowledge_base_id: uuid.UUID | None = None


class ChatRequest(BaseModel):
    message: str
    thread_id: uuid.UUID | None = None
    knowledge_base_id: uuid.UUID | None = None
    system_prompt: str | None = None


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    sources: list[SourceAttribution] | None = None
    model_name: str | None = None
    created_at: datetime
    updated_at: datetime


class ThreadSummaryRead(BaseModel):
    id: uuid.UUID
    title: str
    knowledge_base_id: uuid.UUID | None = None
    message_count: int
    created_at: datetime
    updated_at: datetime


class ChatThreadRead(BaseModel):
    id: uuid.UUID
    title: str
    knowledge_base_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageRead]


class ChatResponse(BaseModel):
    thread: ChatThreadRead
    assistant_message: ChatMessageRead
