import Link from "next/link";

import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";

type DocumentDetailHeaderProps = {
  sourceName: string;
  title: string;
  status: string;
};

export default function DocumentDetailHeader({
  sourceName,
  title,
  status,
}: DocumentDetailHeaderProps) {
  return (
    <>
      <Link
        href="/documents"
        className="document-back-link"
      >
        ← Back to documents
      </Link>

      <header className="documents-header document-detail-header ui-card">
        <div className="ui-card-header">
          <div>
            <p className="documents-eyebrow">
              Document Intelligence
            </p>

            <h1 className="ui-card-title">
              {sourceName}
            </h1>

            <p className="ui-card-description">
              {title}
            </p>
          </div>

          <DocumentStatusBadge status={status} />
        </div>
      </header>
    </>
  );
}