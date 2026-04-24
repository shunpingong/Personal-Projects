"use client";

import { startTransition, useEffect, useRef, useState } from "react";

import {
  createKnowledgeBase,
  getThread,
  listDocuments,
  listKnowledgeBases,
  listThreads,
  sendMessage,
  uploadDocument,
} from "@/lib/api";
import type {
  ChatMessage,
  KnowledgeBase,
  SourceDocument,
  ThreadSummary,
} from "@/lib/types";

function formatError(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Something went wrong.";
}

export function useChatWorkspace() {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const documentsRequestIdRef = useRef(0);

  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [documentKnowledgeBaseId, setDocumentKnowledgeBaseId] = useState<string | null>(null);
  const [manualKnowledgeBaseId, setManualKnowledgeBaseId] = useState<string | null>(null);
  const [systemPrompt, setSystemPrompt] = useState("");

  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isCreatingKnowledgeBase, setIsCreatingKnowledgeBase] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeChatKnowledgeBase =
    knowledgeBases.find((item) => item.id === manualKnowledgeBaseId) ?? null;
  const activeDocumentKnowledgeBase =
    knowledgeBases.find((item) => item.id === documentKnowledgeBaseId) ?? null;

  async function refreshThreads() {
    const nextThreads = await listThreads();
    startTransition(() => {
      setThreads(nextThreads);
    });
  }

  async function refreshDocuments(knowledgeBaseId: string | null) {
    const requestId = documentsRequestIdRef.current + 1;
    documentsRequestIdRef.current = requestId;

    if (!knowledgeBaseId) {
      if (requestId !== documentsRequestIdRef.current) {
        return;
      }

      startTransition(() => {
        setDocuments([]);
      });
      return;
    }

    const nextDocuments = await listDocuments(knowledgeBaseId);
    if (requestId !== documentsRequestIdRef.current) {
      return;
    }

    startTransition(() => {
      setDocuments(nextDocuments);
    });
  }

  useEffect(() => {
    let cancelled = false;

    async function runBootstrap() {
      setIsBootstrapping(true);
      setError(null);

      try {
        const [nextThreads, nextKnowledgeBases] = await Promise.all([
          listThreads(),
          listKnowledgeBases(),
        ]);

        if (cancelled) {
          return;
        }

        startTransition(() => {
          setThreads(nextThreads);
          setKnowledgeBases(nextKnowledgeBases);
          setDocumentKnowledgeBaseId((current) =>
            current && nextKnowledgeBases.some((knowledgeBase) => knowledgeBase.id === current)
              ? current
              : null,
          );
        });

        await refreshDocuments(null);
      } catch (nextError) {
        if (!cancelled) {
          setError(formatError(nextError));
        }
      } finally {
        if (!cancelled) {
          setIsBootstrapping(false);
        }
      }
    }

    void runBootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  async function selectDocumentKnowledgeBase(knowledgeBaseId: string) {
    setError(null);
    setDocumentKnowledgeBaseId(knowledgeBaseId || null);

    try {
      await refreshDocuments(knowledgeBaseId || null);
    } catch (nextError) {
      setError(formatError(nextError));
    }
  }

  async function selectChatKnowledgeBase(knowledgeBaseId: string | null) {
    setError(null);
    setManualKnowledgeBaseId(knowledgeBaseId);
    setSelectedThreadId(null);
    setMessages([]);
  }

  async function selectThread(threadId: string) {
    setError(null);

    try {
      const thread = await getThread(threadId);
      startTransition(() => {
        setSelectedThreadId(thread.id);
        setMessages(thread.messages);
        setManualKnowledgeBaseId(thread.knowledge_base_id ?? null);
        if (thread.knowledge_base_id) {
          setDocumentKnowledgeBaseId(thread.knowledge_base_id);
        }
      });

      if (thread.knowledge_base_id) {
        await refreshDocuments(thread.knowledge_base_id);
      }
    } catch (nextError) {
      setError(formatError(nextError));
    }
  }

  function startNewThread() {
    setSelectedThreadId(null);
    setMessages([]);
    setError(null);
  }

  async function handleCreateKnowledgeBase(name: string, description: string) {
    setIsCreatingKnowledgeBase(true);
    setError(null);

    try {
      const knowledgeBase = await createKnowledgeBase({
        name,
        description: description || null,
      });

      startTransition(() => {
        setKnowledgeBases((current) => [knowledgeBase, ...current]);
        setDocumentKnowledgeBaseId(knowledgeBase.id);
        setDocuments([]);
      });
    } catch (nextError) {
      setError(formatError(nextError));
    } finally {
      setIsCreatingKnowledgeBase(false);
    }
  }

  async function handleUploadDocument(file: File) {
    if (!documentKnowledgeBaseId) {
      setError("Select a knowledge base in the document library before uploading.");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      await uploadDocument(documentKnowledgeBaseId, file);
      await refreshDocuments(documentKnowledgeBaseId);
    } catch (nextError) {
      setError(formatError(nextError));
    } finally {
      setIsUploading(false);
    }
  }

  async function handleSendMessage(content: string) {
    const trimmedContent = content.trim();
    if (!trimmedContent) {
      return;
    }

    const optimisticMessage: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: trimmedContent,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setIsSending(true);
    setError(null);
    setMessages((current) => [...current, optimisticMessage]);

    try {
      const response = await sendMessage({
        message: trimmedContent,
        thread_id: selectedThreadId,
        knowledge_base_id: manualKnowledgeBaseId,
        system_prompt: systemPrompt || null,
      });

      startTransition(() => {
        setSelectedThreadId(response.thread.id);
        setMessages(response.thread.messages);
        setManualKnowledgeBaseId(response.thread.knowledge_base_id ?? null);
        if (response.thread.knowledge_base_id) {
          setDocumentKnowledgeBaseId((current) => current ?? response.thread.knowledge_base_id ?? null);
        }
      });

      await refreshThreads();
    } catch (nextError) {
      setMessages((current) =>
        current.filter((message) => message.id !== optimisticMessage.id),
      );
      setError(formatError(nextError));
    } finally {
      setIsSending(false);
    }
  }

  return {
    activeChatKnowledgeBase,
    activeDocumentKnowledgeBase,
    documentKnowledgeBaseId,
    documents,
    error,
    isBootstrapping,
    isCreatingKnowledgeBase,
    isSending,
    isUploading,
    knowledgeBases,
    manualKnowledgeBaseId,
    messages,
    selectedThreadId,
    systemPrompt,
    threads,
    setSystemPrompt,
    handleCreateKnowledgeBase,
    handleSendMessage,
    handleUploadDocument,
    selectChatKnowledgeBase,
    selectDocumentKnowledgeBase,
    selectThread,
    startNewThread,
  };
}
