"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

import {
  DocumentListItem,
  getDocuments,
  uploadDocument,
} from "@/lib/api/documents";

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

  function getStatusClass(status: string) {
    return `document-status document-status-${status.toLowerCase()}`;
  }

  function getMetadataValue(
    document: DocumentListItem,
    key: string,
  ): string {
    const value = document.metadata?.[key];

    return value === undefined || value === null
      ? "-"
      : String(value);
  }

  return (
    <main className="documents-page">
      <div className="documents-shell">
        <header className="documents-header">
          <div>
            <p className="documents-eyebrow">Knowledge Base</p>
            <h1>Document Intelligence</h1>
            <p>
              Upload enterprise documents and monitor their indexing status.
            </p>
          </div>
        </header>

        <section className="document-upload-form">
          <div className="document-section-heading">
            <h2>Upload Document</h2>
            <p>
              Supported formats: TXT, PDF, and DOCX.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="document-file-field">
              <label htmlFor="document-file">Document</label>
              <input
                id="document-file"
                type="file"
                accept=".txt,.pdf,.docx"
                onChange={handleFileChange}
              />
            </div>

            <div className="document-form-grid">
              <label className="document-field">
                <span>Department</span>
                <input
                  type="text"
                  value={department}
                  onChange={(event) => setDepartment(event.target.value)}
                  placeholder="e.g. HR"
                />
              </label>

              <label className="document-field">
                <span>Document Type</span>
                <input
                  type="text"
                  value={documentType}
                  onChange={(event) =>
                    setDocumentType(event.target.value)
                  }
                  placeholder="e.g. Policy"
                />
              </label>

              <label className="document-field">
                <span>Version</span>
                <input
                  type="text"
                  value={version}
                  onChange={(event) => setVersion(event.target.value)}
                  placeholder="e.g. 1.0"
                />
              </label>

              <label className="document-field">
                <span>Access Level</span>
                <input
                  type="text"
                  value={accessLevel}
                  onChange={(event) =>
                    setAccessLevel(event.target.value)
                  }
                  placeholder="e.g. internal"
                />
              </label>
            </div>

            {uploadError && (
              <div className="document-error">
                {uploadError}
              </div>
            )}

            {uploadSuccess && (
              <div className="document-success">
                {uploadSuccess}
              </div>
            )}

            <button
              type="submit"
              className="document-upload-button"
              disabled={isUploading}
            >
              {isUploading ? "Processing..." : "Upload Document"}
            </button>
          </form>
        </section>

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
              {isLoadingDocuments ? "Refreshing..." : "Refresh"}
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
            <div className="documents-table-wrapper">
              <table className="documents-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Type</th>
                    <th>Department</th>
                    <th>Version</th>
                    <th>Access</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {documents.map((document) => (
                    <tr key={document.id}>
                      <td>
                        <div className="document-name">
                          {document.source_name}
                        </div>
                        <div className="document-title">
                          {document.title}
                        </div>
                      </td>

                      <td>
                        {document.source_type.toUpperCase()}
                      </td>

                      <td>
                        {getMetadataValue(document, "department")}
                      </td>

                      <td>
                        {getMetadataValue(document, "version")}
                      </td>

                      <td>
                        {getMetadataValue(document, "access_level")}
                      </td>

                      <td>
                        <span className={getStatusClass(document.status)}>
                          {document.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

