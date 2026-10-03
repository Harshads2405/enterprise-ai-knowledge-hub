import type { DocumentListItem } from "@/lib/api/documents";

import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";

type DocumentTableProps = {
  documents: DocumentListItem[];
};

function getMetadataValue(
  document: DocumentListItem,
  key: string,
): string {
  const value = document.metadata?.[key];

  return value === undefined || value === null
    ? "-"
    : String(value);
}

export default function DocumentTable({
  documents,
}: DocumentTableProps) {
  return (
    <div className="documents-table-wrapper ui-panel">
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
                {getMetadataValue(
                  document,
                  "access_level",
                )}
              </td>

              <td>
                <DocumentStatusBadge
                  status={document.status}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}