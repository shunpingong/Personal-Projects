from __future__ import annotations

from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict


class RetrievedChunk(TypedDict):
    document_id: str
    filename: str
    snippet: str
    score: float
    knowledge_base_id: str | None
    knowledge_base_name: str | None


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    manual_knowledge_base_id: str | None
    system_prompt: str
    question: str
    route: Literal["retrieve", "direct"]
    retrieval_scope_ids: list[str]
    retrieved_chunks: list[RetrievedChunk]
    sources: list[RetrievedChunk]
    answer: str
