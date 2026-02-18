import { useState } from "react";
import { Send } from "lucide-react";

export default function ChatInput({ sendMessage, disabled }) {
  const [text, setText] = useState("");

  function handleSend() {
    if (!text.trim()) return;
    sendMessage(text);
    setText("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div
      data-testid="chat-input-container"
      className="px-4 py-3 flex items-center gap-3 relative z-10"
      style={{ background: "#202c33" }}
    >
      <input
        data-testid="chat-message-input"
        value={text}
        disabled={disabled}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Connecting..." : "Type a message..."}
        className="flex-1 px-4 py-3 rounded-lg text-sm focus:outline-none focus:ring-1 transition-all"
        style={{
          background: "#2a3942",
          color: "#e9edef",
          border: "none",
        }}
      />

      <button
        data-testid="send-message-button"
        disabled={disabled || !text.trim()}
        onClick={handleSend}
        className="p-3 rounded-lg transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
        style={{ background: "#00a884", color: "#fff" }}
      >
        <Send size={18} />
      </button>
    </div>
  );
}
