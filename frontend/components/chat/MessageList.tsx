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
  return (
    <div className="chat-messages">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onFeedback={onFeedback}
        />
      ))}

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