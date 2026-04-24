"use client";

import { useEffect, useRef } from "react";

import { MessageBubble } from "@/components/chat/message-bubble";
import type { ChatMessage } from "@/lib/types";

type ChatTranscriptProps = {
  messages: ChatMessage[];
  isSending: boolean;
};

export function ChatTranscript({ messages, isSending }: ChatTranscriptProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, isSending]);

  if (!messages.length) {
    return (
      <div className="transcriptEmpty">
        <h3>Ready for the first question.</h3>
        <p>
          Ask a question to start a source-backed conversation, or upload documents to
          expand what the assistant can cite.
        </p>
      </div>
    );
  }

  return (
    <div className="transcript">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {isSending ? (
        <div className="typingIndicator" role="status" aria-live="polite" aria-label="Assistant is responding">
          <span />
          <span />
          <span />
        </div>
      ) : null}

      <div ref={endRef} />
    </div>
  );
}
