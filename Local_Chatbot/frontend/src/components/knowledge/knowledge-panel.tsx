"use client";

import { useState } from "react";

import type { KnowledgeBase, SourceDocument } from "@/lib/types";

type KnowledgePanelProps = {
  activeChatKnowledgeBase: KnowledgeBase | null;
  activeDocumentKnowledgeBase: KnowledgeBase | null;
  documentKnowledgeBaseId: string | null;
  documents: SourceDocument[];
  error?: string | null;
  isCreatingKnowledgeBase: boolean;
  isUploading: boolean;
  knowledgeBases: KnowledgeBase[];
  manualKnowledgeBaseId: string | null;
  onCreateKnowledgeBase: (name: string, description: string) => Promise<void>;
  onSelectChatKnowledgeBase: (knowledgeBaseId: string | null) => Promise<void>;
  onSelectDocumentKnowledgeBase: (knowledgeBaseId: string) => Promise<void>;
  onUploadDocument: (file: File) => Promise<void>;
};

export function KnowledgePanel({
  activeChatKnowledgeBase,
  activeDocumentKnowledgeBase,
  documentKnowledgeBaseId,
  documents,
  error,
  isCreatingKnowledgeBase,
  isUploading,
  knowledgeBases,
  manualKnowledgeBaseId,
  onCreateKnowledgeBase,
  onSelectChatKnowledgeBase,
  onSelectDocumentKnowledgeBase,
  onUploadDocument,
}: KnowledgePanelProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const readyDocuments = documents.filter((document) => document.status === "ready").length;

  async function submitKnowledgeBase() {
    if (!name.trim()) {
      return;
    }

    await onCreateKnowledgeBase(name, description);
    setName("");
    setDescription("");
  }

  return (
    <section className="panel panelCompact panelFill">
      <div className="panelHeading panelHeading--compact">
        <div>
          <p className="eyebrow">Knowledge Operations</p>
          <h3>Libraries and routing</h3>
        </div>
        <div className="heroStats">
          <span className="statusPill">
            {activeChatKnowledgeBase ? activeChatKnowledgeBase.name : "Automatic routing"}
          </span>
          <span className="statusPill">{readyDocuments} ready</span>
        </div>
      </div>

      <div className="managementLayout">
        <div className="managementColumn">
          <label className="fieldLabel">
            Chat routing
            <select
              className="fieldControl"
              value={manualKnowledgeBaseId ?? ""}
              onChange={(event) =>
                void onSelectChatKnowledgeBase(event.target.value || null)
              }
            >
              <option value="">Automatic routing across all libraries</option>
              {knowledgeBases.map((knowledgeBase) => (
                <option key={knowledgeBase.id} value={knowledgeBase.id}>
                  {knowledgeBase.name}
                </option>
              ))}
            </select>
          </label>

          <p className="mutedCopy">
            Leave chat on automatic to let the router choose the best library, or pin
            one library for the next focused conversation.
          </p>

          <div className="panelDivider" />

          <label className="fieldLabel">
            Document library
            <select
              className="fieldControl"
              value={documentKnowledgeBaseId ?? ""}
              onChange={(event) => void onSelectDocumentKnowledgeBase(event.target.value)}
            >
              {knowledgeBases.length ? (
                <option value="">Select a knowledge base</option>
              ) : (
                <option value="">No knowledge bases yet</option>
              )}
              {knowledgeBases.map((knowledgeBase) => (
                <option key={knowledgeBase.id} value={knowledgeBase.id}>
                  {knowledgeBase.name}
                </option>
              ))}
            </select>
          </label>

          <div className="panelDivider" />

          <label className="fieldLabel">
            Create knowledge base
            <input
              className="fieldControl"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Revenue operations"
            />
          </label>

          <label className="fieldLabel">
            Description
            <textarea
              className="fieldControl fieldControl--textarea"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Summarize the documents and topics this library should cover."
              rows={3}
            />
          </label>

          <button
            type="button"
            className="secondaryButton"
            onClick={() => void submitKnowledgeBase()}
            disabled={isCreatingKnowledgeBase}
          >
            {isCreatingKnowledgeBase ? "Creating..." : "Add knowledge base"}
          </button>
        </div>

        <div className="managementColumn managementColumn--wide">
          <label className="uploadDropzone">
            <input
              type="file"
              accept=".txt,.md,.markdown,.json,.pdf"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) {
                  void onUploadDocument(file);
                  event.target.value = "";
                }
              }}
              disabled={isUploading || !documentKnowledgeBaseId}
            />
            <strong>{isUploading ? "Uploading..." : "Upload documents"}</strong>
            <span>Accepted formats: .txt, .md, .json, and .pdf.</span>
          </label>

          <section className="documentShelf">
            <div className="documentShelfHeader">
              <div>
                <p className="eyebrow">Indexed Documents</p>
                <strong>
                  {activeDocumentKnowledgeBase
                    ? activeDocumentKnowledgeBase.name
                    : "No knowledge base selected"}
                </strong>
              </div>
              <span className="statusPill">{documents.length} docs</span>
            </div>

            <div className="documentList scrollRegion">
              {documents.length ? (
                documents.map((document) => (
                  <article key={document.id} className="documentCard">
                    <div className="documentCardHeader">
                      <strong>{document.filename}</strong>
                      <span className={`docStatus docStatus--${document.status}`}>
                        {document.status}
                      </span>
                    </div>
                    <p>{document.chunk_count} chunks indexed</p>
                    {document.error_message ? <p>{document.error_message}</p> : null}
                  </article>
                ))
              ) : (
                <p className="mutedCopy">
                  {activeDocumentKnowledgeBase
                    ? "No documents have been indexed in this library yet. Upload content to make it available for retrieval."
                    : "Select a library to review indexed documents or upload new files."}
                </p>
              )}
            </div>
          </section>
        </div>
      </div>

      {error ? <div className="errorBanner" role="alert">{error}</div> : null}
    </section>
  );
}
