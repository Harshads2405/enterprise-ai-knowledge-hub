"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  Citation,
  ConversationResponse,
  createConversation,
  getConversationMessages,
  getConversations,
  sendConversationMessage,
} from "@/lib/api/conversations";
import { createFeedback } from "@/lib/api/feedback";

const ORGANIZATION_ID = 9;
const USER_ID = 9;

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Citation[];
  messageId?: number;
  feedback?: "positive" | "negative";
  feedbackSubmitting?: boolean;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I’m your Enterprise AI Knowledge & Operations Copilot. How can I help you?",
    },
  ]);

  const [conversations, setConversations] = useState<
    ConversationResponse[]
  >([]);

  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadConversations = async () => {
      setIsLoadingConversations(true);

      try {
        const data = await getConversations(
          ORGANIZATION_ID,
          USER_ID,
        );

        setConversations(data);
      } catch (err) {
        console.error("Failed to load conversations:", err);
      } finally {
        setIsLoadingConversations(false);
      }
    };

    loadConversations();
  }, []);

  function handleNewConversation() {
    setConversationId(null);

    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          "Hello! I’m your Enterprise AI Knowledge & Operations Copilot. How can I help you?",
      },
    ]);

    setInput("");
    setError("");
  }

  async function handleSelectConversation(
    selectedConversationId: number,
  ) {
    if (isLoading) {
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      const storedMessages = await getConversationMessages(
        selectedConversationId,
      );

      const loadedMessages: Message[] = storedMessages.map(
        (message) => {
          const metadata = message.metadata ?? {};

          const sources = Array.isArray(metadata.sources)
            ? (metadata.sources as Citation[])
            : undefined;

          return {
            id: `${message.role}-${message.message_id}`,
            role: message.role,
            content: message.content,
            sources,
            messageId: message.message_id,
          };
        },
      );

      setConversationId(selectedConversationId);

      setMessages(
        loadedMessages.length > 0
          ? loadedMessages
          : [
              {
                id: "welcome",
                role: "assistant",
                content:
                  "Hello! I’m your Enterprise AI Knowledge & Operations Copilot. How can I help you?",
              },
            ],
      );
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to load the conversation.";

      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  const handleFeedback = async (
    messageId: string,
    backendMessageId: number | undefined,
    rating: "positive" | "negative",
  ) => {
    if (!backendMessageId) {
      return;
    }

    setMessages((currentMessages) =>
      currentMessages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              feedbackSubmitting: true,
            }
          : message,
      ),
    );

    try {
      await createFeedback({
        message_id: backendMessageId,
        user_id: USER_ID,
        rating,
      });

      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === messageId
            ? {
                ...message,
                feedback: rating,
                feedbackSubmitting: false,
              }
            : message,
        ),
      );
    } catch (error) {
      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === messageId
            ? {
                ...message,
                feedbackSubmitting: false,
              }
            : message,
        ),
      );

      console.error("Failed to submit feedback:", error);
    }
  };

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
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

      const updatedConversations = await getConversations(
        ORGANIZATION_ID,
        USER_ID,
      );

      setConversations(updatedConversations);

      const assistantMessage: Message = {
        id: `assistant-${response.message_id}`,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        messageId: response.message_id,
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);
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
        <aside className="conversation-sidebar">
          <div className="conversation-sidebar-header">
            <div>
              <p className="chat-eyebrow">Workspace</p>
              <h2>Conversations</h2>
            </div>

            <button
              type="button"
              className="new-conversation-button"
              onClick={handleNewConversation}
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
                    handleSelectConversation(conversation.id)
                  }
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

        <section className="chat-main">
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

                  {message.role === "assistant" && message.messageId && (
                    <div className="message-feedback">
                      {message.feedback !== "negative" && (
                        <button
                          type="button"
                          className={`feedback-button ${
                            message.feedback === "positive" ? "selected" : ""
                          }`}
                          onClick={() =>
                            handleFeedback(
                              message.id,
                              message.messageId,
                              "positive",
                            )
                          }
                          disabled={message.feedbackSubmitting}
                          aria-label="Helpful response"
                          title="Helpful"
                        >
                          👍
                        </button>
                      )}

                      {message.feedback !== "positive" && (
                        <button
                          type="button"
                          className={`feedback-button ${
                            message.feedback === "negative" ? "selected" : ""
                          }`}
                          onClick={() =>
                            handleFeedback(
                              message.id,
                              message.messageId,
                              "negative",
                            )
                          }
                          disabled={message.feedbackSubmitting}
                          aria-label="Unhelpful response"
                          title="Not helpful"
                        >
                          👎
                        </button>
                      )}
                    </div>
                  )}

                  {message.sources &&
                    message.sources.length > 0 && (
                      <div className="message-sources">
                        <p className="sources-title">
                          Sources
                        </p>

                        {message.sources.map(
                          (source, index) => (
                            <div
                              key={`${source.document_id}-${
                                source.chunk_id ?? index
                              }`}
                              className="source-item"
                            >
                              <div className="source-item-header">
                                <span className="source-item-title">
                                  {source.document_title ??
                                    source.source_name ??
                                    `Document ${source.document_id}`}
                                </span>

                                {source.page !== undefined &&
                                  source.page !== null && (
                                    <small>
                                      Page {source.page}
                                    </small>
                                  )}
                              </div>

                              {source.chunk_index !==
                                undefined && (
                                <span className="source-item-chunk">
                                  Chunk {source.chunk_index}
                                </span>
                              )}

                              <div className="source-item-scores">
                                {source.retrieval_score !==
                                  undefined && (
                                  <span className="source-item-score">
                                    Retrieval:{" "}
                                    {source.retrieval_score.toFixed(
                                      2,
                                    )}
                                  </span>
                                )}

                                {source.reranker_score !==
                                  undefined &&
                                  source.reranker_score !==
                                    null && (
                                    <span className="source-item-score">
                                      Reranker:{" "}
                                      {source.reranker_score.toFixed(
                                        2,
                                      )}
                                    </span>
                                  )}
                              </div>
                            </div>
                          ),
                        )}
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

          <form
            className="chat-input-area"
            onSubmit={handleSubmit}
          >
            <input
              type="text"
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
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
      </section>
    </main>
  );
}