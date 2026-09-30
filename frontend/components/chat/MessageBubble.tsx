import CitationList from "@/components/chat/CitationList";
import FeedbackButtons from "@/components/chat/FeedbackButtons";
import type {
  FeedbackHandler,
  Message,
} from "@/components/chat/types";

type MessageBubbleProps = {
  message: Message;
  onFeedback: FeedbackHandler;
};

export default function MessageBubble({
  message,
  onFeedback,
}: MessageBubbleProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div
      className={`message-row ${
        isAssistant
          ? "message-row-assistant"
          : "message-row-user"
      }`}
    >
      <div
        className={`message-bubble ${
          isAssistant
            ? "message-assistant"
            : "message-user"
        }`}
      >
        <p>{message.content}</p>

        {isAssistant && message.messageId && (
          <FeedbackButtons
            messageId={message.id}
            backendMessageId={message.messageId}
            feedback={message.feedback}
            feedbackSubmitting={message.feedbackSubmitting}
            onFeedback={onFeedback}
          />
        )}

        {isAssistant &&
          message.sources &&
          message.sources.length > 0 && (
            <CitationList sources={message.sources} />
          )}
      </div>
    </div>
  );
}