"use client";

import { useState } from "react";

import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatTranscript } from "@/components/chat/chat-transcript";
import { ThreadList } from "@/components/chat/thread-list";
import { KnowledgePanel } from "@/components/knowledge/knowledge-panel";
import { useChatWorkspace } from "@/hooks/use-chat-workspace";

type WorkspaceTab = "chat" | "knowledge" | "threads" | "controls";

const workspaceTabs: Array<{
  id: WorkspaceTab;
  label: string;
  description: string;
}> = [
  { id: "chat", label: "Chat", description: "Sources and replies" },
  { id: "knowledge", label: "Knowledge", description: "Libraries and uploads" },
  { id: "threads", label: "Threads", description: "Saved sessions" },
  { id: "controls", label: "Prompt", description: "Assistant override" },
];

function formatActivity(value: string | null | undefined): string {
  if (!value) {
    return "No recent activity";
  }

  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function ChatShell() {
  const workspace = useChatWorkspace();
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("chat");
  const currentThread =
    workspace.threads.find((thread) => thread.id === workspace.selectedThreadId) ?? null;

  function startThreadAndOpenChat() {
    workspace.startNewThread();
    setActiveTab("chat");
  }

  return (
    <section className="workspaceFrame">
      <nav className="workspaceTabBar" aria-label="Workspace tabs">
        {workspaceTabs.map((tab) => (
          <button
            key={tab.id}
            id={`workspace-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`workspace-panel-${tab.id}`}
            className={`tabButton ${activeTab === tab.id ? "tabButton--active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <strong>{tab.label}</strong>
            <span>{tab.description}</span>
          </button>
        ))}
      </nav>

      <div className="workspaceViewport">
        {activeTab === "chat" ? (
          <section
            id="workspace-panel-chat"
            role="tabpanel"
            aria-labelledby="workspace-tab-chat"
            className="tabPanel tabPanel--chat"
          >
            <section className="panel panelCompact chatToolbarPanel">
              <div className="chatToolbar">
                <div>
                  <p className="eyebrow">Local Chatbot</p>
                  <strong className="chatToolbarTitle">
                    {currentThread ? currentThread.title : "Ready for a new conversation"}
                  </strong>
                </div>

                <div className="chatToolbarMeta">
                  <span className="statusPill">
                    {workspace.activeChatKnowledgeBase
                      ? workspace.activeChatKnowledgeBase.name
                      : "Automatic routing"}
                  </span>
                  <span className="statusPill">{workspace.knowledgeBases.length} libraries</span>
                  <span className="statusPill">
                    {workspace.systemPrompt ? "Custom prompt" : "Default prompt"}
                  </span>
                  <button
                    type="button"
                    className="ghostButton"
                    onClick={startThreadAndOpenChat}
                  >
                    New thread
                  </button>
                </div>
              </div>

              {workspace.error ? <div className="errorBanner" role="alert">{workspace.error}</div> : null}
            </section>

            <section className="panel panelFill transcriptPanel">
              {workspace.isBootstrapping ? (
                <div className="transcriptEmpty">
                  <h3>Preparing your workspace...</h3>
                  <p>Loading libraries, saved conversations, and retrieval settings.</p>
                </div>
              ) : (
                <ChatTranscript
                  messages={workspace.messages}
                  isSending={workspace.isSending}
                />
              )}
            </section>

            <section className="panel panelCompact composerPanel">
              <ChatComposer
                disabled={workspace.isBootstrapping || workspace.isSending}
                pending={workspace.isSending}
                onSend={workspace.handleSendMessage}
              />
            </section>
          </section>
        ) : null}

        {activeTab === "knowledge" ? (
          <section
            id="workspace-panel-knowledge"
            role="tabpanel"
            aria-labelledby="workspace-tab-knowledge"
            className="tabPanel tabPanel--knowledge"
          >
            <KnowledgePanel
              activeChatKnowledgeBase={workspace.activeChatKnowledgeBase}
              activeDocumentKnowledgeBase={workspace.activeDocumentKnowledgeBase}
              documentKnowledgeBaseId={workspace.documentKnowledgeBaseId}
              documents={workspace.documents}
              error={workspace.error}
              isCreatingKnowledgeBase={workspace.isCreatingKnowledgeBase}
              isUploading={workspace.isUploading}
              knowledgeBases={workspace.knowledgeBases}
              manualKnowledgeBaseId={workspace.manualKnowledgeBaseId}
              onCreateKnowledgeBase={workspace.handleCreateKnowledgeBase}
              onSelectChatKnowledgeBase={workspace.selectChatKnowledgeBase}
              onSelectDocumentKnowledgeBase={workspace.selectDocumentKnowledgeBase}
              onUploadDocument={workspace.handleUploadDocument}
            />
          </section>
        ) : null}

        {activeTab === "threads" ? (
          <section
            id="workspace-panel-threads"
            role="tabpanel"
            aria-labelledby="workspace-tab-threads"
            className="tabPanel tabPanel--threads"
          >
            <ThreadList
              threads={workspace.threads}
              selectedThreadId={workspace.selectedThreadId}
              onSelectThread={workspace.selectThread}
              onNewThread={startThreadAndOpenChat}
            />

            <section className="panel panelCompact panelFill detailPanel">
              <div className="panelHeading panelHeading--compact">
                <div>
                  <p className="eyebrow">Conversation Details</p>
                  <h3>Selected thread</h3>
                </div>

                <button
                  type="button"
                  className="primaryButton"
                  onClick={() => setActiveTab("chat")}
                >
                  Open chat
                </button>
              </div>

              <div className="detailStack">
                <article className="detailCard">
                  <span className="eyebrow">Current thread</span>
                  <strong>{currentThread ? currentThread.title : "New conversation"}</strong>
                  <p>
                    {currentThread
                      ? `Updated ${formatActivity(currentThread.updated_at)}`
                      : "Start a new conversation or reopen a previous one."}
                  </p>
                </article>

                <article className="detailCard">
                  <span className="eyebrow">Retrieval scope</span>
                  <strong>
                    {workspace.activeChatKnowledgeBase
                      ? workspace.activeChatKnowledgeBase.name
                      : "Automatic across all libraries"}
                  </strong>
                  <p>{workspace.messages.length} messages are loaded in the active thread.</p>
                </article>

                <article className="detailCard">
                  <span className="eyebrow">Recent activity</span>
                  <strong>{formatActivity(currentThread?.updated_at)}</strong>
                  <p>Use this view to reopen work quickly before jumping back into chat.</p>
                </article>
              </div>

              <div className="actionRow">
                <button
                  type="button"
                  className="secondaryButton"
                  onClick={startThreadAndOpenChat}
                >
                  New thread
                </button>
                <button
                  type="button"
                  className="ghostButton"
                  onClick={() => setActiveTab("knowledge")}
                >
                  Open knowledge
                </button>
              </div>

              {workspace.error ? <div className="errorBanner" role="alert">{workspace.error}</div> : null}
            </section>
          </section>
        ) : null}

        {activeTab === "controls" ? (
          <section
            id="workspace-panel-controls"
            role="tabpanel"
            aria-labelledby="workspace-tab-controls"
            className="tabPanel tabPanel--controls"
          >
            <section className="panel panelCompact panelFill controlsPanel">
              <div className="panelHeading panelHeading--compact">
                <div>
                  <p className="eyebrow">Assistant Settings</p>
                  <h2>Instruction layer</h2>
                </div>

                <div className="actionRow">
                  <button
                    type="button"
                    className="ghostButton"
                    onClick={() => workspace.setSystemPrompt("")}
                    disabled={!workspace.systemPrompt}
                  >
                    Clear custom prompt
                  </button>
                  <button
                    type="button"
                    className="primaryButton"
                    onClick={() => setActiveTab("chat")}
                  >
                    Back to chat
                  </button>
                </div>
              </div>

              <div className="controlsLayout">
                <label className="fieldLabel">
                  System prompt override
                  <textarea
                    className="fieldControl fieldControl--textarea fieldControl--prompt"
                    rows={8}
                    value={workspace.systemPrompt}
                    onChange={(event) => workspace.setSystemPrompt(event.target.value)}
                    placeholder="Add a temporary instruction override for the next reply."
                  />
                </label>

                <div className="detailStack">
                  <article className="detailCard">
                    <span className="eyebrow">Prompt state</span>
                    <strong>
                      {workspace.systemPrompt ? "Custom instructions active" : "Workspace default in use"}
                    </strong>
                    <p>
                      Leave this blank to rely on the standard assistant guidance, or set
                      a temporary override for a focused thread.
                    </p>
                  </article>

                  <article className="detailCard">
                    <span className="eyebrow">Knowledge scope</span>
                    <strong>
                      {workspace.activeChatKnowledgeBase
                        ? workspace.activeChatKnowledgeBase.name
                        : "Automatic across all libraries"}
                    </strong>
                    <p>
                      {workspace.activeDocumentKnowledgeBase
                        ? `${workspace.documents.length} documents are available in the current library.`
                        : "Open Knowledge to review document libraries and routing scope."}
                    </p>
                  </article>

                  <article className="detailCard">
                    <span className="eyebrow">Thread state</span>
                    <strong>{currentThread ? currentThread.title : "New conversation"}</strong>
                    <p>{workspace.messages.length} messages are staged in the active thread.</p>
                  </article>
                </div>
              </div>

              {workspace.error ? <div className="errorBanner" role="alert">{workspace.error}</div> : null}
            </section>
          </section>
        ) : null}
      </div>
    </section>
  );
}
