type ThreadListProps = {
  threads: {
    id: string;
    title: string;
    message_count: number;
    updated_at: string;
  }[];
  selectedThreadId: string | null;
  onSelectThread: (threadId: string) => Promise<void>;
  onNewThread: () => void;
};

export function ThreadList({
  threads,
  selectedThreadId,
  onSelectThread,
  onNewThread,
}: ThreadListProps) {
  return (
    <section className="panel panelCompact panelFill">
      <div className="panelHeading panelHeading--compact">
        <div>
          <p className="eyebrow">Threads</p>
          <h3>Saved conversations</h3>
        </div>
        <div className="actionRow">
          <span className="statusPill">{threads.length} total</span>
          <button type="button" className="ghostButton" onClick={onNewThread}>
            New thread
          </button>
        </div>
      </div>

      <div className="threadList scrollRegion">
        {threads.length ? (
          threads.map((thread) => (
            <button
              key={thread.id}
              type="button"
              className={`threadCard ${
                selectedThreadId === thread.id ? "threadCard--active" : ""
              }`}
              aria-pressed={selectedThreadId === thread.id}
              onClick={() => void onSelectThread(thread.id)}
            >
              <strong>{thread.title}</strong>
              <span>{thread.message_count} messages</span>
              <span>{new Date(thread.updated_at).toLocaleString()}</span>
            </button>
          ))
        ) : (
          <p className="mutedCopy">No saved conversations yet.</p>
        )}
      </div>
    </section>
  );
}
