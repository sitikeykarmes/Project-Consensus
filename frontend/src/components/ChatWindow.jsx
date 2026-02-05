import { useEffect, useRef, useState } from "react";
import ChatHeader from "./ChatHeader";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";

export default function ChatWindow({ group }) {
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  // Connect WebSocket when group changes
  useEffect(() => {
    setMessages([]);

    socketRef.current = new WebSocket(
      `ws://localhost:8001/ws/${group.id}/Kartikey`,
    );

    socketRef.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (
        msg.type === "user_message" ||
        msg.type === "agent_response" ||
        msg.type === "consensus" ||
        msg.type === "system"
      ) {
        setMessages((prev) => [...prev, msg]);
      }
    };

    return () => {
      socketRef.current.close();
    };
  }, [group.id]);

  // Send message
  function sendMessage(text) {
    socketRef.current.send(JSON.stringify({ message: text }));
  }

  return (
    <div className="flex-1 flex flex-col">
      <ChatHeader group={group} />

      {/* Messages */}
      <div className="flex-1 bg-[#efeae2] px-6 py-4 overflow-y-auto space-y-3">
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
      </div>

      <ChatInput sendMessage={sendMessage} />
    </div>
  );
}
