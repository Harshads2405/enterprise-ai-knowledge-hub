"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  Citation,
  ConversationResponse,
  createConversation,
  getConversationMessages,
  getConversations,
  sendConversationMessage,
} from "@/lib/api/conversations";

import { createFeedback } from "@/lib/api/feedback";

import ConversationSidebar from "@/components/chat/ConversationSidebar";
import ChatHeader from "@/components/chat/ChatHeader";
import MessageList from "@/components/chat/MessageList";
import ChatInput from "@/components/chat/ChatInput";

import type {
  FeedbackRating,
  Message,
} from "@/components/chat/types";

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

  const [conversations, setConversations] = useState<
    ConversationResponse[]
  >([]);

  const [input, setInput] = useState("");
  const [conversationId, setConversationId] =
    useState<number | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] =
    useState(false);

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
        console.error(
          "Failed to load conversations:",
          err,
        );
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
      const storedMessages =
        await getConversationMessages(
          selectedConversationId,
        );

      const loadedMessages: Message[] =
        storedMessages.map((message) => {
          const metadata = message.metadata ?? {};

          const sources = Array.isArray(
            metadata.sources,
          )
            ? (metadata.sources as Citation[])
            : undefined;

          return {
            id: `${message.role}-${message.message_id}`,
            role: message.role,
            content: message.content,
            sources,
            messageId: message.message_id,
          };
        });

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
  rating: FeedbackRating,
) => {
  const message = messages.find((item) => item.id === messageId);

  if (!backendMessageId || message?.feedbackSubmitting) {
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

    console.error(
      "Failed to submit feedback:",
      error,
    );
  }
};

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const content = input.trim();

    if (!content || isLoading) return;

    if (content.length > 4000) {
      setError("Message cannot exceed 4000 characters.");
      return;
    }

    setError("");

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
    };

    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    setInput("");
    setIsLoading(true);

    try {
      let activeConversationId =
        conversationId;

      if (!activeConversationId) {
        const conversation =
          await createConversation({
            organization_id: ORGANIZATION_ID,
            user_id: USER_ID,
            title: content.slice(0, 80),
          });

        activeConversationId = conversation.id;
        setConversationId(activeConversationId);
      }

      const response =
        await sendConversationMessage(
          activeConversationId,
          {
            content,
          },
        );

      const updatedConversations =
        await getConversations(
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
          content:
            "I couldn't process your request.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="chat-page">
      <section className="chat-shell">

        <ConversationSidebar
          conversations={conversations}
          conversationId={conversationId}
          isLoadingConversations={
            isLoadingConversations
          }
          isLoading={isLoading}
          onNewConversation={
            handleNewConversation
          }
          onSelectConversation={
            handleSelectConversation
          }
        />

        <section className="chat-main">

          <ChatHeader
            conversationId={conversationId}
          />

          <MessageList
            messages={messages}
            isLoading={isLoading}
            onFeedback={handleFeedback}
          />

          {error && (
            <div
              className="chat-error"
              role="alert"
            >
              {error}
            </div>
          )}

          <ChatInput
            input={input}
            isLoading={isLoading}
            onInputChange={setInput}
            onSubmit={handleSubmit}
          />

        </section>
      </section>
    </main>
  );
}