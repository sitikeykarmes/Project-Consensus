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
      className="px-4 pb-6 pt-2 flex items-center justify-center relative z-10 w-full"
      style={{ background: "transparent" }}
    >
      <div 
        className="flex items-center gap-2 w-full max-w-3xl p-1.5 rounded-3xl"
        style={{ 
          background: "var(--bg-input)", 
          border: "1px solid var(--border)",
          boxShadow: "0 4px 12px rgba(0,0,0,0.5)"
        }}
      >
        <input
          data-testid="chat-message-input"
          value={text}
          disabled={disabled}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "Connecting..." : "Message Consensus..."}
          className="flex-1 px-4 py-2.5 bg-transparent text-sm focus:outline-none"
          style={{
            color: "var(--text-primary)",
          }}
        />

        <button
          data-testid="send-message-button"
          disabled={disabled || !text.trim()}
          onClick={handleSend}
          className="w-9 h-9 rounded-full transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center shrink-0 mr-1"
          style={{ background: "var(--accent)", color: "var(--bg-app)" }}
        >
          <Send size={16} strokeWidth={2.5} style={{ marginLeft: "-2px" }} />
        </button>
      </div>
    </div>
  );
}
