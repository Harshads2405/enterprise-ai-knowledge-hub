import type { Citation } from "@/lib/api/conversations";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Citation[];
  messageId?: number;
  feedback?: "positive" | "negative";
  feedbackSubmitting?: boolean;
};

export type FeedbackRating = "positive" | "negative";

export type FeedbackHandler = (
  messageId: string,
  backendMessageId: number | undefined,
  rating: FeedbackRating,
) => void;