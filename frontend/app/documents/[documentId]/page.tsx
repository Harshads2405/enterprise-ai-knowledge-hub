"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import {
  DocumentDetail,
  getDocument,
} from "@/lib/api/documents";

export default function DocumentDetailPage() {
  const params = useParams();
  const documentId = Number(params.documentId);

  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!Number.isInteger(documentId) || documentId <= 0) {
      setError("Invalid document ID.");
      setIsLoading(false);
      return;
    }

    async function loadDocument() {
      try {
        const data = await getDocument(documentId);
        setDocument(data);
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Failed to load document.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDocument();
  }, [documentId]);

  if (isLoading) {
    return (
      <main className="documents-page">
        <div className="documents-shell">
          <div className="documents-empty-state">
            Loading document...
          </div>
        </div>
      </main>
    );
  }

  if (error || !document) {
    return (
      <main className="documents-page">
        <div className="documents-shell">
          <Link
            href="/documents"
            className="document-back-link"
          >
            ← Back to documents
          </Link>

          <div className="document-error">
            {error || "Document not found."}
          </div>
        </div>
      </main>
    );
  }

  const metadata = document.metadata ?? {};

  return (
    <main className="documents-page">
      <div className="documents-shell">
        <Link
          href="/documents"
          className="document-back-link"
        >
          ← Back to documents
        </Link>

        <header className="documents-header document-detail-header">
          <div>
            <p className="documents-eyebrow">
              Document Intelligence
            </p>

            <h1>{document.source_name}</h1>

            <p>
              {document.title}
            </p>
          </div>

          <span
            className={`document-status document-status-${document.status.toLowerCase()}`}
          >
            {document.status}
          </span>
        </header>

        <section className="document-detail-card">
          <div className="document-detail-heading">
            <h2>Document Information</h2>
          </div>

          <div className="document-detail-grid">
            <div className="document-detail-item">
              <span>Document ID</span>
              <strong>{document.id}</strong>
            </div>

            <div className="document-detail-item">
              <span>File Type</span>
              <strong>
                {document.source_type.toUpperCase()}
              </strong>
            </div>

            <div className="document-detail-item">
              <span>Department</span>
              <strong>
                {String(metadata.department ?? "-")}
              </strong>
            </div>

            <div className="document-detail-item">
              <span>Document Type</span>
              <strong>
                {String(metadata.document_type ?? "-")}
              </strong>
            </div>

            <div className="document-detail-item">
              <span>Version</span>
              <strong>
                {String(metadata.version ?? "-")}
              </strong>
            </div>

            <div className="document-detail-item">
              <span>Access Level</span>
              <strong>
                {String(metadata.access_level ?? "-")}
              </strong>
            </div>

            <div className="document-detail-item">
              <span>Created</span>
              <strong>
                {new Date(document.created_at).toLocaleString()}
              </strong>
            </div>

            <div className="document-detail-item">
              <span>Last Updated</span>
              <strong>
                {new Date(document.updated_at).toLocaleString()}
              </strong>
            </div>
          </div>
        </section>

        <section className="document-detail-card">
          <div className="document-detail-heading">
            <h2>Processing Status</h2>
          </div>

          <div className="document-processing-status">
            <span
              className={`document-status document-status-${document.status.toLowerCase()}`}
            >
              {document.status}
            </span>

            <p>
              This document has been processed by the document
              ingestion pipeline.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}