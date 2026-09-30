type DocumentStatusBadgeProps = {
  status: string;
};

export default function DocumentStatusBadge({
  status,
}: DocumentStatusBadgeProps) {
  return (
    <span
      className={`document-status document-status-${status.toLowerCase()}`}
    >
      {status}
    </span>
  );
}