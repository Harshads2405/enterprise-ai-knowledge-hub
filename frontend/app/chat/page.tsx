"use client";

import { FormEvent, useState } from "react";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      content:
        "Hello! I’m your Enterprise AI Copilot. Ask me a question about your organization's knowledge.",
    },
  ]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const question = input.trim();

    if (!question) {
      return;
    }

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: question,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
  };

  return (
    <main className="chat-page">
      <header className="chat-header">
        <div>
          <span className="chat-eyebrow">Enterprise AI</span>
          <h1>AI Copilot</h1>
        </div>

        <div className="connection-status">
          <span className="status-dot" />
          Ready
        </div>
      </header>

      <section className="chat-container">
        <div className="messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-row ${message.role}`}
            >
              <div className="message">
                <span className="message-role">
                  {message.role === "user" ? "You" : "Copilot"}
                </span>

                <p>{message.content}</p>
              </div>
            </div>
          ))}
        </div>

        <form className="chat-input-area" onSubmit={handleSubmit}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask your organization anything..."
            rows={1}
            aria-label="Message"
          />

          <button type="submit" disabled={!input.trim()}>
            Send
          </button>
        </form>
      </section>
    </main>
  );
}
