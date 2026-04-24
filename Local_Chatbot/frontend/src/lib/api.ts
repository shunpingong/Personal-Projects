import type {
  ChatResponse,
  ChatThread,
  KnowledgeBase,
  SourceDocument,
  ThreadSummary,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

function extractErrorMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  return null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const isFormData = init?.body instanceof FormData;

  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const contentType = response.headers.get("Content-Type") ?? "";
    if (contentType.includes("application/json")) {
      const errorPayload = (await response.json().catch(() => null)) as unknown;
      const detail = extractErrorMessage(errorPayload);
      if (detail) {
        throw new Error(detail);
      }

      throw new Error(`Request failed with status ${response.status}`);
    }

    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function listThreads(): Promise<ThreadSummary[]> {
  return request<ThreadSummary[]>("/threads");
}

export function getThread(threadId: string): Promise<ChatThread> {
  return request<ChatThread>(`/threads/${threadId}`);
}

export function createThread(payload: {
  title?: string | null;
  knowledge_base_id?: string | null;
}): Promise<ChatThread> {
  return request<ChatThread>("/threads", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function sendMessage(payload: {
  message: string;
  thread_id?: string | null;
  knowledge_base_id?: string | null;
  system_prompt?: string | null;
}): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  return request<KnowledgeBase[]>("/knowledge-bases");
}

export function createKnowledgeBase(payload: {
  name: string;
  description?: string | null;
}): Promise<KnowledgeBase> {
  return request<KnowledgeBase>("/knowledge-bases", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listDocuments(knowledgeBaseId: string): Promise<SourceDocument[]> {
  return request<SourceDocument[]>(`/knowledge-bases/${knowledgeBaseId}/documents`);
}

export function uploadDocument(
  knowledgeBaseId: string,
  file: File,
): Promise<SourceDocument> {
  const body = new FormData();
  body.append("file", file);

  return request<SourceDocument>(
    `/knowledge-bases/${knowledgeBaseId}/documents`,
    {
      method: "POST",
      body,
    },
  );
}
