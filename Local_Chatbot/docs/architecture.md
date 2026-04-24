# Architecture

## Runtime Layers

### Frontend

- `src/app/`
  Route shell and global styling.
- `src/components/`
  UI composition for chat, threads, and knowledge-base controls.
- `src/hooks/use-chat-workspace.ts`
  Browser-side state management and API orchestration.
- `src/lib/api.ts`
  Thin HTTP client for the backend contract.

### Backend

- `app/api/`
  Versioned FastAPI route registration and HTTP handlers.
- `app/core/`
  Settings and lifespan wiring.
- `app/db/`
  SQLAlchemy base, session factory, and ORM models.
- `app/services/`
  Application orchestration for threads and document ingestion.
- `app/modules/rag/`
  Retrieval, provider factories, loaders, and LangGraph workflow logic.

## Persistence Model

PostgreSQL is split into two concerns:

- relational application data
  - `knowledge_bases`
  - `source_documents`
  - `chat_threads`
  - `chat_messages`
- LangGraph checkpoint persistence
  - created and managed by `AsyncPostgresSaver`

Qdrant stores two vector concerns:

- a chunk collection for document retrieval
- a KB-routing collection with one summary record per knowledge base

## Request Flow

### Document ingestion

1. Frontend uploads a file to `/knowledge-bases/{id}/documents`.
2. Backend stores the raw file under `backend/storage/uploads/...`.
3. `KnowledgeService` extracts text, chunks it, and pushes chunks into Qdrant.
4. `KnowledgeService` refreshes the KB routing record so automatic chat reflects the new document set.
5. PostgreSQL stores the document metadata, routing preview, and indexing status.

### Chat turn

1. Frontend posts a message to `/chat`.
2. `ChatService` persists the user message and resolves the active thread.
3. Thread scope is fixed once the thread exists. A stored `knowledge_base_id` acts as a manual override; `null` keeps the thread in automatic multi-KB mode.
4. `RAGGraphService` invokes the LangGraph workflow using the thread ID as the checkpoint key.
5. The graph:
   - prepares the turn state
   - determines retrieval scope from either the manual override or the dedicated KB-routing index
   - retrieves matching chunks from Qdrant for the chosen KB scope
   - builds the final prompt
   - calls the chat model
6. The assistant message and source attributions are persisted in PostgreSQL.
7. Frontend receives the refreshed thread payload and re-renders the transcript.

## Extension Points

### Better agent behavior

Edit `backend/app/modules/rag/graph/builder.py` to add:

- query rewriting
- tool routing
- multi-step planning
- reflection / critique nodes
- human-in-the-loop interrupts

### Retrieval changes

Edit `backend/app/modules/rag/vector_store.py` to add:

- hybrid dense/sparse retrieval
- metadata filtering beyond knowledge-base ID
- re-ranking
- collection-per-tenant strategies

### Ingestion changes

Edit `backend/app/modules/rag/loaders.py` and `backend/app/services/knowledge_service.py` to add:

- more file types
- OCR
- async background ingestion
- duplicate detection
- per-document parsing rules

### Frontend behavior

Edit `frontend/src/hooks/use-chat-workspace.ts` and `frontend/src/components/chat/` to add:

- optimistic assistant streaming
- message editing / retry
- side-by-side source inspection
- prompt presets
- admin controls for ingestion health
