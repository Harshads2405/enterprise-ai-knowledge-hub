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
    <section className="document-upload-form ui-card">
      <div className="ui-card-header">
        <div>
          <h2 className="ui-card-title">Upload Document</h2>
          <p className="ui-card-description">
            Supported formats: TXT, PDF, and DOCX.
          </p>
        </div>
      </div>

      <div className="ui-card-body">
        <form onSubmit={onSubmit}>
          <div className="document-file-field">
            <label
              htmlFor="document-file"
              className="ui-label"
            >
              Document
            </label>

            <input
              id="document-file"
              type="file"
              accept=".txt,.pdf,.docx"
              onChange={onFileChange}
              className="ui-input"
            />

            {file && (
              <small className="ui-field-help">
                Selected: {file.name}
              </small>
            )}
          </div>

          <div className="document-form-grid">
            <label className="document-field">
              <span className="ui-label">Department</span>

              <input
                type="text"
                value={department}
                onChange={(event) =>
                  onDepartmentChange(event.target.value)
                }
                placeholder="e.g. HR"
                className="ui-input"
              />
            </label>

            <label className="document-field">
              <span className="ui-label">Document Type</span>

              <input
                type="text"
                value={documentType}
                onChange={(event) =>
                  onDocumentTypeChange(event.target.value)
                }
                placeholder="e.g. Policy"
                className="ui-input"
              />
            </label>

            <label className="document-field">
              <span className="ui-label">Version</span>

              <input
                type="text"
                value={version}
                onChange={(event) =>
                  onVersionChange(event.target.value)
                }
                placeholder="e.g. 1.0"
                className="ui-input"
              />
            </label>

            <label className="document-field">
              <span className="ui-label">Access Level</span>

              <input
                type="text"
                value={accessLevel}
                onChange={(event) =>
                  onAccessLevelChange(event.target.value)
                }
                placeholder="e.g. internal"
                className="ui-input"
              />
            </label>
          </div>

          {uploadError && (
            <div
              className="ui-feedback ui-feedback-error"
              role="alert"
            >
              {uploadError}
            </div>
          )}

          {uploadSuccess && (
            <div
              className="ui-feedback ui-feedback-success"
              role="status"
            >
              {uploadSuccess}
            </div>
          )}

          <div className="document-upload-actions">
            <button
              type="submit"
              className="ui-button ui-button-primary"
              disabled={isUploading}
            >
              {isUploading
                ? "Processing..."
                : "Upload Document"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}