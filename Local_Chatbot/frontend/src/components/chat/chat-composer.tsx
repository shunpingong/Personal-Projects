"use client";

import { KeyboardEvent, useState } from "react";

type ChatComposerProps = {
  disabled: boolean;
  pending: boolean;
  onSend: (message: string) => Promise<void>;
};

export function ChatComposer({
  disabled,
  pending,
  onSend,
}: ChatComposerProps) {
  const [draft, setDraft] = useState("");

  async function submit() {
    const nextDraft = draft.trim();
    if (!nextDraft || disabled) {
      return;
    }

    await onSend(nextDraft);
    setDraft("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  }

  return (
    <div className="composer">
      <label className="srOnly" htmlFor="chat-draft">
        Message
      </label>
      <textarea
        id="chat-draft"
        className="composerInput"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={handleKeyDown}
        aria-describedby="chat-draft-hint"
        placeholder="Ask about a policy, compare sources, or trace an answer back to its documents."
        disabled={disabled}
        rows={3}
      />

      <div className="composerFooter">
        <p id="chat-draft-hint">Enter sends. Shift+Enter adds a line break.</p>
        <button
          type="button"
          className="primaryButton"
          onClick={() => void submit()}
          disabled={disabled || !draft.trim()}
        >
          {pending ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}
