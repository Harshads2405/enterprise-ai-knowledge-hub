const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Citation = {
  document_id: number;
  document_title?: string;
  source_name?: string;
  page?: number;
  chunk_id?: number;
  content?: string;
  score?: number;
};

export type ConversationResponse = {
  id: number;
  organization_id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ConversationRAGResponse = {
  message_id: number;
  conversation_id: number;
  role: string;
  answer: string;
  sources: Citation[];
  should_clarify: boolean;
  clarification_question: string;
  clarification_options: Array<{
    label: string;
    topic: string;
  }>;
  metadata: Record<string, unknown>;
};

type CreateConversationRequest = {
  organization_id: number;
  user_id: number;
  title?: string;
};

type SendMessageRequest = {
  content: string;
  limit?: number;
  department?: string;
};

async function requestJson<T>(
  path: string,
  body: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;

    try {
      const errorBody = await response.json();

      if (typeof errorBody?.detail === "string") {
        message = errorBody.detail;
      }
    } catch {
      // Keep the default error message when the response is not JSON.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function createConversation(
  payload: CreateConversationRequest,
): Promise<ConversationResponse> {
  return requestJson<ConversationResponse>(
    "/api/v1/conversations",
    payload,
  );
}

export async function sendConversationMessage(
  conversationId: number,
  payload: SendMessageRequest,
): Promise<ConversationRAGResponse> {
  return requestJson<ConversationRAGResponse>(
    `/api/v1/conversations/${conversationId}/messages`,
    payload,
  );
}

export async function getConversations(
  organizationId: number,
  userId: number,
): Promise<ConversationResponse[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/conversations?organization_id=${organizationId}&user_id=${userId}`,
  );

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;

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

  return response.json() as Promise<ConversationResponse[]>;
}

export async function getConversation(
  conversationId: number,
): Promise<ConversationResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/conversations/${conversationId}`,
  );

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;

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

  return response.json() as Promise<ConversationResponse>;
}

export type ConversationMessage = {
  message_id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  metadata: Record<string, unknown>;
};

export async function getConversationMessages(
  conversationId: number,
): Promise<ConversationMessage[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/conversations/${conversationId}/messages`,
  );

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;

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

  return response.json() as Promise<ConversationMessage[]>;
}
