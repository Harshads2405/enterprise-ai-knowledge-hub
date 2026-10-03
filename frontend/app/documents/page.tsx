"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import {
  DocumentListItem,
  getDocuments,
  uploadDocument,
} from "@/lib/api/documents";

import DocumentUploadForm from "@/components/documents/DocumentUploadForm";
import DocumentTable from "@/components/documents/DocumentTable";
import AppShell from "@/components/layout/AppShell";

const ORGANIZATION_ID = 9;
const USER_ID = 9;

const ALLOWED_EXTENSIONS = [".txt", ".pdf", ".docx"];

export default function DocumentsPage() {
  const [file, setFile] = useState<File | null>(null);

  const [department, setDepartment] = useState("");
  const [documentType, setDocumentType] = useState("");
  const [version, setVersion] = useState("");
  const [accessLevel, setAccessLevel] = useState("");

  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);
  const [documentsError, setDocumentsError] = useState("");

  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");

  async function loadDocuments() {
    setIsLoadingDocuments(true);
    setDocumentsError("");

    try {
      const data = await getDocuments(ORGANIZATION_ID, USER_ID);
      setDocuments(data);
    } catch (error) {
      setDocumentsError(
        error instanceof Error
          ? error.message
          : "Failed to load documents.",
      );
    } finally {
      setIsLoadingDocuments(false);
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;

    setFile(selectedFile);
    setUploadError("");
    setUploadSuccess("");

    if (!selectedFile) {
      return;
    }

    const extension = selectedFile.name
      .substring(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setUploadError(
        "Unsupported file type. Please select a TXT, PDF, or DOCX file.",
      );
      setFile(null);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setUploadError("");
    setUploadSuccess("");

    if (!file) {
      setUploadError("Please select a document.");
      return;
    }

    setIsUploading(true);

    try {
      const result = await uploadDocument({
        file,
        organization_id: ORGANIZATION_ID,
        uploaded_by: USER_ID,
        department: department || undefined,
        document_type: documentType || undefined,
        version: version || undefined,
        access_level: accessLevel || undefined,
      });

      setUploadSuccess(
        `Document processed successfully: ${result.source_name} (${result.status})`,
      );

      setFile(null);
      setDepartment("");
      setDocumentType("");
      setVersion("");
      setAccessLevel("");

      await loadDocuments();
    } catch (error) {
      setUploadError(
        error instanceof Error
          ? error.message
          : "Document upload failed.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <AppShell>
      <div className="documents-page">
        <div className="documents-shell">
          <header className="documents-header">
            <div>
              <p className="documents-eyebrow">
                Knowledge Base
              </p>

              <h1>Document Intelligence</h1>

              <p>
                Upload enterprise documents and monitor their indexing status.
              </p>
            </div>
          </header>

          <DocumentUploadForm
            file={file}
            department={department}
            documentType={documentType}
            version={version}
            accessLevel={accessLevel}
            isUploading={isUploading}
            uploadError={uploadError}
            uploadSuccess={uploadSuccess}
            onFileChange={handleFileChange}
            onDepartmentChange={setDepartment}
            onDocumentTypeChange={setDocumentType}
            onVersionChange={setVersion}
            onAccessLevelChange={setAccessLevel}
            onSubmit={handleSubmit}
          />

          <section className="documents-list-section">
            <div className="documents-list-header">
              <div>
                <h2>Documents</h2>

                <p>
                  Documents currently indexed for this organization.
                </p>
              </div>

              <button
                type="button"
                className="document-refresh-button"
                onClick={() => void loadDocuments()}
                disabled={isLoadingDocuments}
              >
                {isLoadingDocuments
                  ? "Refreshing..."
                  : "Refresh"}
              </button>
            </div>

            {documentsError && (
              <div className="document-error">
                {documentsError}
              </div>
            )}

            {isLoadingDocuments ? (
              <div className="documents-empty-state">
                Loading documents...
              </div>
            ) : documents.length === 0 ? (
              <div className="documents-empty-state">
                No documents have been uploaded yet.
              </div>
            ) : (
              <DocumentTable documents={documents} />
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}