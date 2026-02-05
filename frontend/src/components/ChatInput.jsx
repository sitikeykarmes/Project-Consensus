import { useState } from "react";

export default function ChatInput({ sendMessage }) {
  const [text, setText] = useState("");

  function handleSend() {
    if (!text.trim()) return;
    sendMessage(text);
    setText("");
  }

  return (
    <div className="h-16 flex items-center px-4 bg-[#f0f2f5] gap-3">
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type a message..."
        className="flex-1 px-4 py-2 rounded-full outline-none bg-white"
      />

      <button
        onClick={handleSend}
        className="bg-green-600 text-white px-4 py-2 rounded-full"
      >
        Send
      </button>
    </div>
  );
}
