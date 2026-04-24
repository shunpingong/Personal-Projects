from __future__ import annotations

import json
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Any, Literal, cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from openai import APIConnectionError

from app.core.config import Settings
from app.modules.rag.errors import raise_provider_unavailable
from app.modules.rag.graph.state import AgentState, RetrievedChunk
from app.modules.rag.providers import build_chat_model
from app.modules.rag.vector_store import QdrantVectorStoreManager


@dataclass(slots=True)
class GraphResult:
    answer: str
    sources: list[RetrievedChunk]


class RAGGraphService:
    def __init__(self, settings: Settings, vector_store: QdrantVectorStoreManager):
        self.settings = settings
        self.vector_store = vector_store
        self.model = build_chat_model(settings)
        self._graph: Any | None = None
        self._checkpointer_cm: AbstractAsyncContextManager[Any] | None = None
        self._checkpointer: AsyncPostgresSaver | None = None

    async def startup(self) -> None:
        self._checkpointer_cm = AsyncPostgresSaver.from_conn_string(
            self.settings.langgraph_database_url
        )
        self._checkpointer = await self._checkpointer_cm.__aenter__()
        await self._checkpointer.setup()
        self._graph = self._build_graph()

    async def shutdown(self) -> None:
        if self._checkpointer_cm is not None:
            await self._checkpointer_cm.__aexit__(None, None, None)

    async def ask(
        self,
        *,
        thread_id: str,
        message: str,
        knowledge_base_id: str | None,
        system_prompt: str | None,
    ) -> GraphResult:
        graph = self._require_graph()
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=message)],
                "manual_knowledge_base_id": knowledge_base_id,
                "system_prompt": system_prompt or self.settings.default_system_prompt,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
        return GraphResult(
            answer=result["answer"],
            sources=cast(list[RetrievedChunk], result.get("sources", [])),
        )

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("prepare_turn", self._prepare_turn)
        builder.add_node("determine_scope", self._determine_scope)
        builder.add_node("retrieve_context", self._retrieve_context)
        builder.add_node("generate_answer", self._generate_answer)

        builder.add_edge(START, "prepare_turn")
        builder.add_edge("prepare_turn", "determine_scope")
        builder.add_conditional_edges(
            "determine_scope",
            self._route_turn,
            {
                "retrieve": "retrieve_context",
                "direct": "generate_answer",
            },
        )
        builder.add_edge("retrieve_context", "generate_answer")
        builder.add_edge("generate_answer", END)

        return builder.compile(checkpointer=self._checkpointer)

    def _prepare_turn(self, state: AgentState) -> dict[str, Any]:
        latest_message = state["messages"][-1]
        question = latest_message.content if isinstance(latest_message.content, str) else str(latest_message.content)
        return {
            "question": question,
            "route": "direct",
            "retrieval_scope_ids": [],
            "retrieved_chunks": [],
            "sources": [],
        }

    def _route_turn(self, state: AgentState) -> Literal["retrieve", "direct"]:
        return state["route"]

    async def _determine_scope(self, state: AgentState) -> dict[str, Any]:
        manual_knowledge_base_id = state.get("manual_knowledge_base_id")
        if manual_knowledge_base_id:
            return {
                "route": "retrieve",
                "retrieval_scope_ids": [manual_knowledge_base_id],
            }

        retrieval_scope_ids = await self.vector_store.discover_routing_scope(
            query=state["question"],
            limit=self.settings.kb_routing_top_k,
            score_threshold=self.settings.kb_routing_score_threshold,
            score_margin=self.settings.kb_routing_score_margin,
        )
        return {
            "route": "retrieve" if retrieval_scope_ids else "direct",
            "retrieval_scope_ids": retrieval_scope_ids,
        }

    async def _retrieve_context(self, state: AgentState) -> dict[str, Any]:
        results = await self.vector_store.similarity_search(
            query=state["question"],
            knowledge_base_ids=state.get("retrieval_scope_ids") or None,
            limit=self.settings.rag_top_k,
            score_threshold=self.settings.rag_score_threshold,
        )

        sources: list[RetrievedChunk] = []
        for document, score in results:
            metadata = document.metadata
            sources.append(
                RetrievedChunk(
                    document_id=str(metadata.get("source_document_id")),
                    filename=str(metadata.get("filename", "Untitled source")),
                    snippet=document.page_content[:320].strip(),
                    score=round(float(score), 4),
                    knowledge_base_id=str(metadata.get("knowledge_base_id"))
                    if metadata.get("knowledge_base_id")
                    else None,
                    knowledge_base_name=str(metadata.get("knowledge_base_name"))
                    if metadata.get("knowledge_base_name")
                    else None,
                )
            )

        return {
            "retrieved_chunks": sources,
            "sources": sources,
        }

    async def _generate_answer(self, state: AgentState) -> dict[str, Any]:
        prompt_messages = [
            SystemMessage(
                content=self._build_system_prompt(
                    system_prompt=state.get("system_prompt") or self.settings.default_system_prompt,
                    chunks=state.get("retrieved_chunks", []),
                )
            ),
            *state["messages"],
        ]

        try:
            response = await self.model.ainvoke(prompt_messages)
        except APIConnectionError as exc:
            raise_provider_unavailable(provider="Chat model", settings=self.settings, exc=exc)
        answer = self._normalize_content(response.content)
        return {
            "messages": [AIMessage(content=answer)],
            "answer": answer,
        }

    def _build_system_prompt(
        self,
        *,
        system_prompt: str,
        chunks: list[RetrievedChunk],
    ) -> str:
        if not chunks:
            return (
                f"{system_prompt}\n\n"
                "No retrieved documents matched this turn. "
                "Answer from general model knowledge only, and be explicit that retrieval did not provide supporting evidence."
            )

        context_lines = [
            f"[{index + 1}] "
            f"{chunk.get('knowledge_base_name') or chunk.get('knowledge_base_id') or 'Unknown knowledge base'}"
            f" :: {chunk['filename']} (score={chunk['score']})\n{chunk['snippet']}"
            for index, chunk in enumerate(chunks)
        ]
        return (
            f"{system_prompt}\n\n"
            "Use the retrieved context below when answering. If the answer is not supported by "
            "the retrieved context, say that directly.\n\n"
            f"{chr(10).join(context_lines)}"
        )

    def _normalize_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        return json.dumps(content, default=str)

    def _require_graph(self):
        if self._graph is None:
            raise RuntimeError("LangGraph has not been initialized.")
        return self._graph
