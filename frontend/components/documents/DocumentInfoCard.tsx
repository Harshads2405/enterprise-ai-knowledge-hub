type DocumentInfoCardProps = {
  documentId: number;
  sourceType: string;
  department: string;
  documentType: string;
  version: string;
  accessLevel: string;
  createdAt: string;
  updatedAt: string;
};

export default function DocumentInfoCard({
  documentId,
  sourceType,
  department,
  documentType,
  version,
  accessLevel,
  createdAt,
  updatedAt,
}: DocumentInfoCardProps) {
  return (
    <section className="document-detail-card">
      <div className="document-detail-heading">
        <h2>Document Information</h2>
      </div>

      <div className="document-detail-grid">
        <div className="document-detail-item">
          <span>Document ID</span>
          <strong>{documentId}</strong>
        </div>

        <div className="document-detail-item">
          <span>File Type</span>
          <strong>{sourceType.toUpperCase()}</strong>
        </div>

        <div className="document-detail-item">
          <span>Department</span>
          <strong>{department}</strong>
        </div>

        <div className="document-detail-item">
          <span>Document Type</span>
          <strong>{documentType}</strong>
        </div>

        <div className="document-detail-item">
          <span>Version</span>
          <strong>{version}</strong>
        </div>

        <div className="document-detail-item">
          <span>Access Level</span>
          <strong>{accessLevel}</strong>
        </div>

        <div className="document-detail-item">
          <span>Created</span>
          <strong>{createdAt}</strong>
        </div>

        <div className="document-detail-item">
          <span>Last Updated</span>
          <strong>{updatedAt}</strong>
        </div>
      </div>
    </section>
  );
}