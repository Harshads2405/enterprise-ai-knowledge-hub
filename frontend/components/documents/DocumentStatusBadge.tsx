type DocumentStatusBadgeProps = {
  status: string;
};

function getBadgeVariant(status: string): string {
  switch (status.toLowerCase()) {
    case "completed":
    case "processed":
    case "active":
      return "success";

    case "processing":
    case "pending":
      return "warning";

    case "failed":
    case "error":
      return "danger";

    default:
      return "neutral";
  }
}

export default function DocumentStatusBadge({
  status,
}: DocumentStatusBadgeProps) {
  const variant = getBadgeVariant(status);

  return (
    <span className={`ui-badge ui-badge-${variant}`}>
      {status}
    </span>
  );
}