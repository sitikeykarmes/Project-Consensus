import { useEffect, useRef, useState } from "react";
import ChatHeader from "./ChatHeader";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";

export default function ChatWindow({ group }) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [currentUserId, setCurrentUserId] = useState(null);

  const socketRef = useRef(null);

  useEffect(() => {
    if (!group) return;

    setMessages([]);
    setConnected(false);

    // ✅ Get token from localStorage
    const token = localStorage.getItem("token");

    if (!token) {
      alert("❌ You are not logged in!");
      return;
    }

    // ✅ Get current user ID from localStorage
    const userStr = localStorage.getItem("user");
    if (userStr) {
      const userData = JSON.parse(userStr);
      setCurrentUserId(userData.id);
    }

    // ✅ WebSocket URL with token
    const socket = new WebSocket(
      `ws://localhost:8001/ws/${group.id}?token=${token}`,
    );

    socketRef.current = socket;

    socket.onopen = () => {
      console.log("✅ WebSocket Connected");
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);
    };

    socket.onclose = () => {
      console.log("❌ WebSocket Closed");
      setConnected(false);
    };

    socket.onerror = (err) => {
      console.log("⚠️ WebSocket Error:", err);
      setConnected(false);
    };

    return () => {
      socket.close();
    };
  }, [group.id]);

  // ✅ Safe send
  function sendMessage(text) {
    if (!socketRef.current) return;

    if (socketRef.current.readyState !== WebSocket.OPEN) {
      alert("❌ Socket not connected yet!");
      return;
    }

    socketRef.current.send(JSON.stringify({ message: text }));
  }

  return (
    <div className="flex-1 flex flex-col">
      <ChatHeader group={group} />

      {/* Connection status */}
      <div className="text-xs text-center py-1">
        {connected ? (
          <span className="text-green-600">🟢 Connected</span>
        ) : (
          <span className="text-red-500">🔴 Connecting...</span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 bg-[#efeae2] px-6 py-4 overflow-y-auto space-y-3">
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} currentUserId={currentUserId} />
        ))}
      </div>

      {/* Input */}
      <ChatInput sendMessage={sendMessage} disabled={!connected} />
    </div>
  );
}
