import { useEffect, useRef, useState } from "react";

export default function ChatRoom() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const wsRef = useRef(null);

  const roomId = "room1";
  const userName = "Kartikey"; // you can make it dynamic later

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${roomId}/${userName}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("✅ Connected to WebSocket");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      setMessages((prev) => [...prev, data]);
    };

    ws.onclose = () => {
      console.log("❌ WebSocket disconnected");
    };

    return () => ws.close();
  }, []);

  const sendMessage = () => {
    if (!input.trim()) return;

    wsRef.current.send(
      JSON.stringify({
        message: input,
      }),
    );

    setInput("");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-blue-950 text-white">
      <div className="w-full max-w-3xl bg-blue-900 rounded-xl p-6 shadow-lg">
        <h1 className="text-2xl font-bold text-center mb-4">
          🧠 Project Consensus Chat
        </h1>

        {/* Chat Messages */}
        <div className="h-96 overflow-y-auto bg-blue-800 rounded-lg p-4 space-y-3">
          {messages.map((msg, index) => {
            if (msg.type === "user_message") {
              return (
                <div key={index} className="text-right">
                  <div className="inline-block bg-green-600 px-3 py-2 rounded-lg">
                    <b>{msg.user_name}:</b> {msg.content}
                  </div>
                </div>
              );
            }

            if (msg.type === "agent_response") {
              return (
                <div key={index} className="text-left">
                  <div className="inline-block bg-purple-600 px-3 py-2 rounded-lg">
                    🤖 <b>{msg.agent_name}</b>: {msg.content}
                  </div>
                </div>
              );
            }

            if (msg.type === "consensus") {
              return (
                <div key={index} className="text-center">
                  <div className="inline-block bg-yellow-600 text-black px-4 py-2 rounded-lg font-semibold">
                    ✅ Consensus: {msg.content}
                  </div>
                </div>
              );
            }

            if (msg.type === "user_joined") {
              return (
                <div key={index} className="text-center text-gray-300">
                  👤 {msg.user_name} joined the room
                </div>
              );
            }

            if (msg.type === "user_left") {
              return (
                <div key={index} className="text-center text-gray-300">
                  👤 {msg.user_name} left the room
                </div>
              );
            }

            return null;
          })}
        </div>

        {/* Input Box */}
        <div className="flex gap-2 mt-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask something..."
            className="flex-1 px-4 py-2 rounded-lg bg-blue-700 text-white outline-none"
          />
          <button
            onClick={sendMessage}
            className="px-5 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
