import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";

type DocumentProcessingStatusProps = {
  status: string;
};

export default function DocumentProcessingStatus({
  status,
}: DocumentProcessingStatusProps) {
  return (
    <section className="document-detail-card ui-card">
      <div className="ui-card-header">
        <div>
          <h2 className="ui-card-title">
            Processing Status
          </h2>
        </div>
      </div>

      <div className="ui-card-body">
        <div className="document-processing-status">
          <DocumentStatusBadge status={status} />

          <p>
            This document has been processed by the
            document ingestion pipeline.
          </p>
        </div>
      </div>
    </section>
  );
}