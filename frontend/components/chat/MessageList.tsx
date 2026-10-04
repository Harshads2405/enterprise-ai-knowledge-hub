import MessageBubble from "@/components/chat/MessageBubble";
import type {
  FeedbackHandler,
  Message,
} from "@/components/chat/types";

type MessageListProps = {
  messages: Message[];
  isLoading: boolean;
  onFeedback: FeedbackHandler;
};

export default function MessageList({
  messages,
  isLoading,
  onFeedback,
}: MessageListProps) {
  // Empty chat state
  if (messages.length === 0) {
    return (
      <div className="chat-empty-state">
        <span className="chat-empty-eyebrow">
          Enterprise AI Copilot
        </span>

        <h2>How can I help?</h2>

        <p>
          Ask questions about your enterprise knowledge, documents, and
          operations.
        </p>

        <div
          className="chat-empty-capabilities"
          aria-label="Capabilities"
        >
          <span>Search</span>
          <span>Understand</span>
          <span>Act</span>
        </div>
      </div>
    );
  }

  // Messages state
  return (
    <div className="chat-messages">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onFeedback={onFeedback}
        />
      ))}

      {/* Loading state */}
      {isLoading && (
        <div className="message-row message-row-assistant">
          <div className="message-bubble message-assistant">
            <p>Thinking...</p>
          </div>
        </div>
      )}
    </div>
  );
}