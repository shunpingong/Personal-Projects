export type MessageRole = "user" | "assistant" | "system";

export type SourceAttribution = {
  document_id: string;
  filename: string;
  snippet: string;
  score: number;
  knowledge_base_id?: string | null;
  knowledge_base_name?: string | null;
};

export type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string;
  sources?: SourceAttribution[] | null;
  model_name?: string | null;
  created_at: string;
  updated_at: string;
};

export type ChatThread = {
  id: string;
  title: string;
  knowledge_base_id?: string | null;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
};

export type ThreadSummary = {
  id: string;
  title: string;
  knowledge_base_id?: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
};

export type KnowledgeBase = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
};

export type SourceDocument = {
  id: string;
  knowledge_base_id: string;
  filename: string;
  content_type?: string | null;
  checksum: string;
  chunk_count: number;
  status: "processing" | "ready" | "failed";
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

export type ChatResponse = {
  thread: ChatThread;
  assistant_message: ChatMessage;
};
