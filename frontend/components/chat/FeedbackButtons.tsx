import type { FeedbackRating } from "@/components/chat/types";

type FeedbackButtonsProps = {
  messageId: string;
  backendMessageId: number | undefined;
  feedback: FeedbackRating | undefined;
  feedbackSubmitting: boolean | undefined;
  onFeedback: (
    messageId: string,
    backendMessageId: number | undefined,
    rating: FeedbackRating,
  ) => void;
};

export default function FeedbackButtons({
  messageId,
  backendMessageId,
  feedback,
  feedbackSubmitting,
  onFeedback,
}: FeedbackButtonsProps) {
  if (!backendMessageId) {
    return null;
  }

  return (
    <div className="message-feedback">
      {feedback !== "negative" && (
        <button
          type="button"
          className={`feedback-button ${
            feedback === "positive" ? "selected" : ""
          }`}
          onClick={() =>
            onFeedback(messageId, backendMessageId, "positive")
          }
          disabled={feedbackSubmitting}
          aria-label="Helpful response"
          title="Helpful"
        >
          👍
        </button>
      )}

      {feedback !== "positive" && (
        <button
          type="button"
          className={`feedback-button ${
            feedback === "negative" ? "selected" : ""
          }`}
          onClick={() =>
            onFeedback(messageId, backendMessageId, "negative")
          }
          disabled={feedbackSubmitting}
          aria-label="Unhelpful response"
          title="Not helpful"
        >
          👎
        </button>
      )}
    </div>
  );
}