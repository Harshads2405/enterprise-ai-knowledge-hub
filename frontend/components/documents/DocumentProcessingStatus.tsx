import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";

type DocumentProcessingStatusProps = {
  status: string;
};

export default function DocumentProcessingStatus({
  status,
}: DocumentProcessingStatusProps) {
  return (
    <section className="document-detail-card">
      <div className="document-detail-heading">
        <h2>Processing Status</h2>
      </div>

      <div className="document-processing-status">
        <DocumentStatusBadge status={status} />

        <p>
          This document has been processed by the
          document ingestion pipeline.
        </p>
      </div>
    </section>
  );
}