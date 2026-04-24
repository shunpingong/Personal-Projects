# Local_Chatbot

`Local_Chatbot` is a local full-stack boilerplate for building a retrieval-augmented chatbot with:

- a Next.js chat frontend
- a FastAPI backend
- LangGraph state orchestration
- LangChain model and embedding integrations
- PostgreSQL for relational metadata and LangGraph checkpoints
- Qdrant for vector retrieval

Chat now defaults to automatic retrieval across all indexed knowledge bases through a dedicated KB-routing index. Manual knowledge-base selection is still available as an override when you want to pin a thread to one collection.

The repo is intentionally scaffolded for editing. The goal is to give you a solid starting point, not a locked demo.

## What Is Included

- chat UI that renders full user/assistant history
- thread switching and persisted chat history
- knowledge-base creation and document ingestion
- document chunking and vector indexing
- automatic multi-knowledge-base retrieval with a dedicated KB-routing index
- LangGraph workflow with explicit retrieval and answer-generation nodes
- FastAPI project structure split across `core`, `db`, `api`, `modules`, `services`, and `schemas`
- Alembic migration scaffold
- Docker Compose for frontend, backend, PostgreSQL, and Qdrant

## Project Layout

```text
Local_Chatbot/
|-- backend/
|   |-- alembic/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- db/
|   |   |-- modules/
|   |   |-- schemas/
|   |   `-- services/
|   |-- .env.example
|   |-- Dockerfile
|   `-- pyproject.toml
|-- docs/
|   `-- architecture.md
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |-- components/
|   |   |-- hooks/
|   |   `-- lib/
|   |-- .env.example
|   |-- Dockerfile
|   `-- package.json
|-- .gitignore
|-- docker-compose.yml
`-- README.md
```

## Quick Start

### Option 1: Docker Compose

1. Copy `backend/.env.example` to `backend/.env`.
2. Copy `frontend/.env.example` to `frontend/.env.local`.
3. Fill in your LLM and embedding credentials in `backend/.env`.
   If you point `OPENAI_BASE_URL` at a host-local OpenAI-compatible server and run the backend in Docker Desktop, use `http://host.docker.internal:<port>/v1` instead of `http://localhost:<port>/v1`.
4. Run:

```powershell
docker compose up --build
```

The frontend will be available at `http://localhost:3000` and the backend at `http://localhost:8000`.

The frontend now waits for the backend health check before it starts, so the first page load should not race the API boot sequence during `docker compose up`.

The checked-in `.env.example` files keep `localhost` values so the app still works for direct host-machine runs. Docker Compose overrides the backend's database and Qdrant hosts to the internal service names (`postgres` and `qdrant`) at container runtime.

In the UI, chat runs in automatic multi-KB mode by default. Use the knowledge tab only when you want to browse a specific document library or force a manual chat override.

### Option 2: Run Locally

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Supporting services:

- PostgreSQL on `localhost:5432`
- Qdrant on `localhost:6333`

You can still use `docker compose up postgres qdrant` if you only want the data services containerized.

## Configuration

Backend config lives in `backend/app/core/config.py` and reads from `backend/.env`.

Key values to edit first:

- `LLM_MODEL`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `EMBEDDING_MODEL`
- `EMBEDDING_DIMENSIONS`
- `DATABASE_URL`
- `LANGGRAPH_DATABASE_URL`
- `QDRANT_URL`
- `QDRANT_ROUTING_COLLECTION`

If `OPENAI_BASE_URL` is blank, the backend uses the public OpenAI API and the backend container needs outbound internet access. If you use a local OpenAI-compatible server instead, make sure the URL is reachable from the backend runtime, not just from your host machine.

Retrieval behavior:

- If `knowledge_base_id` is sent with `/chat`, that thread is manually scoped to the selected knowledge base.
- If `knowledge_base_id` is omitted, the backend searches a dedicated KB-routing index, selects the strongest KB candidates, and only then runs chunk retrieval inside those KBs.
- Existing threads keep the scope they were created with. The manual override is for new draft threads, not for retargeting an old thread midway through the conversation.
- If no KB produces a strong enough retrieval match, the assistant falls back and states that retrieval did not provide supporting evidence.

Frontend config is a single variable:

- `NEXT_PUBLIC_API_BASE_URL`

## Main Editing Hotspots

- `backend/app/modules/rag/graph/builder.py`
  This is the LangGraph workflow. Add more nodes, tools, or branching here.
- `backend/app/modules/rag/vector_store.py`
  Swap retrieval strategy, filtering, or hybrid search here.
- `backend/app/services/knowledge_service.py`
  Extend ingestion, parsing, deduplication, or chunking here.
- `backend/app/services/chat_service.py`
  Change thread rules, persistence behavior, or request orchestration here.
- `frontend/src/components/chat/chat-shell.tsx`
  Main UI composition layer.
- `frontend/src/hooks/use-chat-workspace.ts`
  Frontend state and API coordination layer.

## Notes

- The current embedding factory is OpenAI-compatible out of the box.
- Chat threads with `knowledge_base_id=null` use automatic multi-KB retrieval. Threads with a stored `knowledge_base_id` are treated as manual overrides.
- Once a thread exists, its retrieval scope stays fixed. Start a new thread if you want to switch between automatic mode and a manual KB override.
- Qdrant collection compatibility is validated from stored collection metadata, so the backend no longer makes a dummy embedding request just to open an existing collection.
- The current graph is a solid RAG baseline, not a full autonomous agent loop.
- LangGraph checkpoints are stored in PostgreSQL, separate from the app's relational tables.
- Qdrant stores both chunk vectors and a second KB-routing collection with one routing record per knowledge base.
- Each routing record is built from KB metadata plus compact document previews so automatic routing does not need a global chunk-level probe.
- Chunk retrieval payload metadata still includes the source knowledge-base ID and name for source attribution.

See `docs/architecture.md` for the system flow and extension map.
