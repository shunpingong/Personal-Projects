import type { ChatMessage } from "@/lib/types";

type MessageBubbleProps = {
  message: ChatMessage;
};

export function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <article className={`messageBubble messageBubble--${message.role}`}>
      <div className="messageMeta">
        <span className="messageRole">{message.role}</span>
        <span className="messageTime">
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      <div className="messageBody">
        {message.content.split("\n").map((line, index) => (
          <p key={`${message.id}-${index}`}>{line || "\u00a0"}</p>
        ))}
      </div>

      {message.sources && message.sources.length > 0 ? (
        <div className="sourceTray">
          {message.sources.map((source, index) => (
            <div key={`${source.document_id}-${index}`} className="sourceCard">
              <div className="sourceCardHeader">
                <span>{source.filename}</span>
                <span>{Math.round(source.score * 100)}% match</span>
              </div>
              {source.knowledge_base_name ? (
                <p className="sourceScope">Knowledge base: {source.knowledge_base_name}</p>
              ) : null}
              <p className="sourceSnippet">{source.snippet}</p>
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}
