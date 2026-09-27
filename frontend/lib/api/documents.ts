const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

export type DocumentUploadResponse = {
  id: number;
  title: string;
  source_type: string;
  source_name: string;
  status: string;
};

export type UploadDocumentRequest = {
  file: File;
  organization_id: number;
  uploaded_by: number;
  department?: string;
  document_type?: string;
  version?: string;
  access_level?: string;
};

export type DocumentListItem = {
  id: number;
  title: string;
  source_type: string;
  source_name: string;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export async function uploadDocument(
  payload: UploadDocumentRequest,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();

  formData.append("file", payload.file);
  formData.append(
    "organization_id",
    String(payload.organization_id),
  );
  formData.append(
    "uploaded_by",
    String(payload.uploaded_by),
  );

  if (payload.department) {
    formData.append("department", payload.department);
  }

  if (payload.document_type) {
    formData.append("document_type", payload.document_type);
  }

  if (payload.version) {
    formData.append("version", payload.version);
  }

  if (payload.access_level) {
    formData.append("access_level", payload.access_level);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents/upload`,
    {
      method: "POST",
      body: formData,
    },
  );

  if (!response.ok) {
    let message = `Upload failed with status ${response.status}.`;

    try {
      const errorBody = await response.json();

      if (typeof errorBody?.detail === "string") {
        message = errorBody.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json() as Promise<DocumentUploadResponse>;
}

export async function getDocuments(
  organizationId: number,
  uploadedBy?: number,
): Promise<DocumentListItem[]> {
  const params = new URLSearchParams({
    organization_id: String(organizationId),
  });

  if (uploadedBy !== undefined) {
    params.set("uploaded_by", String(uploadedBy));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents?${params.toString()}`,
  );

  if (!response.ok) {
    let message = `Failed to load documents with status ${response.status}.`;

    try {
      const errorBody = await response.json();

      if (typeof errorBody?.detail === "string") {
        message = errorBody.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(message);
  }

  return response.json() as Promise<DocumentListItem[]>;
}

