import type { FormEvent } from "react";

const MAX_MESSAGE_LENGTH = 4000;

type ChatInputProps = {
  input: string;
  isLoading: boolean;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function ChatInput({
  input,
  isLoading,
  onInputChange,
  onSubmit,
}: ChatInputProps) {
  const characterCount = input.length;
  const isNearLimit = characterCount >= 3600;
  const isOverLimit = characterCount > MAX_MESSAGE_LENGTH;

  return (
    <form className="chat-input-area" onSubmit={onSubmit}>
      <div className="chat-input-wrapper">
        <input
          type="text"
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder="Ask your enterprise knowledge assistant..."
          disabled={isLoading}
          aria-label="Ask the enterprise knowledge assistant"
          maxLength={MAX_MESSAGE_LENGTH}
        />

        <span
          className={`chat-input-counter ${
            isOverLimit
              ? "chat-input-counter-error"
              : isNearLimit
                ? "chat-input-counter-warning"
                : ""
          }`}
          aria-live="polite"
        >
          {characterCount} / {MAX_MESSAGE_LENGTH}
        </span>
      </div>

      <button
        type="submit"
        disabled={!input.trim() || isLoading || isOverLimit}
      >
        {isLoading ? "Sending..." : "Send"}
      </button>
    </form>
  );
}