import type { ConversationResponse } from "@/lib/api/conversations";

type ConversationSidebarProps = {
  conversations: ConversationResponse[];
  conversationId: number | null;
  isLoadingConversations: boolean;
  isLoading: boolean;
  onNewConversation: () => void;
  onSelectConversation: (
    conversationId: number,
  ) => void;
};

export default function ConversationSidebar({
  conversations,
  conversationId,
  isLoadingConversations,
  isLoading,
  onNewConversation,
  onSelectConversation,
}: ConversationSidebarProps) {
  return (
    <aside className="conversation-sidebar">
      <div className="conversation-sidebar-header">
        <div>
          <p className="chat-eyebrow">Workspace</p>
          <h2>Conversations</h2>
        </div>

        <button
          type="button"
          className="ui-button ui-button-primary ui-button-sm new-conversation-button"
          onClick={onNewConversation}
        >
          + New Chat
        </button>
      </div>

      <div className="conversation-list">
        {isLoadingConversations ? (
          <p className="conversation-list-status">
            Loading conversations...
          </p>
        ) : conversations.length === 0 ? (
          <p className="conversation-list-status">
            No conversations yet.
          </p>
        ) : (
          conversations.map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              className={`conversation-item ${
                conversation.id === conversationId
                  ? "conversation-item-active"
                  : ""
              }`}
              onClick={() =>
                onSelectConversation(conversation.id)
              }
              disabled={isLoading}
            >
              <span className="conversation-item-title">
                {conversation.title}
              </span>

              <span className="conversation-item-id">
                #{conversation.id}
              </span>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}