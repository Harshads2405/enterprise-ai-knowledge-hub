import type { FormEvent } from "react";

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
  return (
    <form
      className="chat-input-area"
      onSubmit={onSubmit}
    >
      <input
        type="text"
        value={input}
        onChange={(event) =>
          onInputChange(event.target.value)
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
  );
}