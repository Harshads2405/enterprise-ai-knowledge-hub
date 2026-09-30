type ChatHeaderProps = {
  conversationId: number | null;
};

export default function ChatHeader({
  conversationId,
}: ChatHeaderProps) {
  return (
    <header className="chat-header">
      <div>
        <p className="chat-eyebrow">Enterprise AI</p>
        <h1>Knowledge & Operations Copilot</h1>
      </div>

      {conversationId && (
        <span className="conversation-status">
          Conversation #{conversationId}
        </span>
      )}
    </header>
  );
}