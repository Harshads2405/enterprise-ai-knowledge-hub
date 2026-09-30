import type { ChangeEvent, FormEvent } from "react";

type DocumentUploadFormProps = {
  file: File | null;
  department: string;
  documentType: string;
  version: string;
  accessLevel: string;
  isUploading: boolean;
  uploadError: string;
  uploadSuccess: string;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onDepartmentChange: (value: string) => void;
  onDocumentTypeChange: (value: string) => void;
  onVersionChange: (value: string) => void;
  onAccessLevelChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function DocumentUploadForm({
  file,
  department,
  documentType,
  version,
  accessLevel,
  isUploading,
  uploadError,
  uploadSuccess,
  onFileChange,
  onDepartmentChange,
  onDocumentTypeChange,
  onVersionChange,
  onAccessLevelChange,
  onSubmit,
}: DocumentUploadFormProps) {
  return (
    <section className="document-upload-form">
      <div className="document-section-heading">
        <h2>Upload Document</h2>
        <p>
          Supported formats: TXT, PDF, and DOCX.
        </p>
      </div>

      <form onSubmit={onSubmit}>
        <div className="document-file-field">
          <label htmlFor="document-file">
            Document
          </label>

          <input
            id="document-file"
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={onFileChange}
          />

          {file && (
            <small>
              Selected: {file.name}
            </small>
          )}
        </div>

        <div className="document-form-grid">
          <label className="document-field">
            <span>Department</span>

            <input
              type="text"
              value={department}
              onChange={(event) =>
                onDepartmentChange(event.target.value)
              }
              placeholder="e.g. HR"
            />
          </label>

          <label className="document-field">
            <span>Document Type</span>

            <input
              type="text"
              value={documentType}
              onChange={(event) =>
                onDocumentTypeChange(event.target.value)
              }
              placeholder="e.g. Policy"
            />
          </label>

          <label className="document-field">
            <span>Version</span>

            <input
              type="text"
              value={version}
              onChange={(event) =>
                onVersionChange(event.target.value)
              }
              placeholder="e.g. 1.0"
            />
          </label>

          <label className="document-field">
            <span>Access Level</span>

            <input
              type="text"
              value={accessLevel}
              onChange={(event) =>
                onAccessLevelChange(event.target.value)
              }
              placeholder="e.g. internal"
            />
          </label>
        </div>

        {uploadError && (
          <div className="document-error" role="alert">
            {uploadError}
          </div>
        )}

        {uploadSuccess && (
          <div className="document-success" role="status">
            {uploadSuccess}
          </div>
        )}

        <button
          type="submit"
          className="document-upload-button"
          disabled={isUploading}
        >
          {isUploading
            ? "Processing..."
            : "Upload Document"}
        </button>
      </form>
    </section>
  );
}