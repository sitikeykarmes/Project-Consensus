import { useState } from "react";
export default function ChatInput({ sendMessage, disabled }) {
  const [text, setText] = useState("");

  function handleSend() {
    if (!text.trim()) return;
    sendMessage(text);
    setText("");
  }

  return (
    <div className="p-3 flex gap-2 border-t">
      <input
        value={text}
        disabled={disabled}
        onChange={(e) => setText(e.target.value)}
        placeholder={disabled ? "Connecting..." : "Type a message"}
        className="flex-1 px-3 py-2 border rounded"
      />

      <button
        disabled={disabled}
        onClick={handleSend}
        className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50"
      >
        Send
      </button>
    </div>
  );
}
