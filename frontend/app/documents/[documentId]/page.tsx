"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import {
  DocumentDetail,
  getDocument,
} from "@/lib/api/documents";

import DocumentDetailHeader from "@/components/documents/DocumentDetailHeader";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import DocumentInfoCard from "@/components/documents/DocumentInfoCard";
import DocumentProcessingStatus from "@/components/documents/DocumentProcessingStatus";

export default function DocumentDetailPage() {
  const params = useParams();
  const documentId = Number(params.documentId);

  const [document, setDocument] =
    useState<DocumentDetail | null>(null);

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
          <DocumentDetailHeader
            sourceName="Document"
            title=""
            status="error"
          />

          <div
            className="document-error"
            role="alert"
          >
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
        <DocumentDetailHeader
          sourceName={document.source_name}
          title={document.title}
          status={document.status}
        />

      <DocumentInfoCard
        documentId={document.id}
        sourceType={document.source_type}
        department={String(metadata.department ?? "-")}
        documentType={String(metadata.document_type ?? "-")}
        version={String(metadata.version ?? "-")}
        accessLevel={String(metadata.access_level ?? "-")}
        createdAt={new Date(
          document.created_at,
        ).toLocaleString()}
        updatedAt={new Date(
          document.updated_at,
        ).toLocaleString()}
      />

    <DocumentProcessingStatus status={document.status} />      </div>
    </main>
  );
}