const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type FeedbackRating = "positive" | "negative";

export type CreateFeedbackRequest = {
  message_id: number;
  user_id: number;
  rating: FeedbackRating;
  comment?: string;
};

export type FeedbackResponse = {
  id: number;
  message_id: number;
  user_id: number;
  rating: FeedbackRating;
  comment: string | null;
  created_at: string;
};

export async function createFeedback(
  payload: CreateFeedbackRequest,
): Promise<FeedbackResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

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

  return response.json() as Promise<FeedbackResponse>;
}
