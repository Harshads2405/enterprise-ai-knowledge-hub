"use client";

import { FormEvent, useState } from "react";

import {
  createConversation,
  sendConversationMessage,
  type Citation,
} from "@/lib/api/conversations";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Citation[];
};

const ORGANIZATION_ID = 9;
const USER_ID = 9;

export default function ChatPage() {
const [messages, setMessages] = useState<Message[]>([
  {
    id: "welcome",
    role: "assistant",
    content:
      "Hello! I’m your Enterprise AI Knowledge & Operations Copilot. How can I help you?",
  },
]);

  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const content = input.trim();

    if (!content || isLoading) {
      return;
    }

    setError("");

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      let activeConversationId = conversationId;

      if (!activeConversationId) {
        const conversation = await createConversation({
          organization_id: ORGANIZATION_ID,
          user_id: USER_ID,
          title: content.slice(0, 80),
        });

        activeConversationId = conversation.id;
        setConversationId(activeConversationId);
      }

      const response = await sendConversationMessage(
        activeConversationId,
        {
          content,
        },
      );

      const assistantMessage: Message = {
        id: `assistant-${response.message_id}`,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong while contacting the backend.";

      setError(message);

      setMessages((current) => [
        ...current,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: "I couldn't process your request.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="chat-page">
      <section className="chat-shell">
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

        <div className="chat-messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-row ${
                message.role === "user"
                  ? "message-row-user"
                  : "message-row-assistant"
              }`}
            >
              <div
                className={`message-bubble ${
                  message.role === "user"
                    ? "message-user"
                    : "message-assistant"
                }`}
              >
                <p>{message.content}</p>

                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <p className="sources-title">Sources</p>

                    {message.sources.map((source, index) => (
                      <div
                        key={`${source.document_id}-${source.chunk_id ?? index}`}
                        className="source-item"
                      >
                        <span>
                          {source.document_title ??
                            source.source_name ??
                            `Document ${source.document_id}`}
                        </span>

                        {source.page !== undefined && (
                          <small>Page {source.page}</small>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message-row message-row-assistant">
              <div className="message-bubble message-assistant">
                <p>Thinking...</p>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="chat-error" role="alert">
            {error}
          </div>
        )}

        <form className="chat-input-area" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask your enterprise knowledge assistant..."
            disabled={isLoading}
          />

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
          >
            {isLoading ? "Sending..." : "Send"}
          </button>
        </form>
      </section>
    </main>
  );
}