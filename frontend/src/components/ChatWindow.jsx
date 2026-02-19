import { useEffect, useRef, useState } from "react";
import ChatHeader from "./ChatHeader";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import ChatInput from "./ChatInput";
import { getWsUrl } from "../api/chatApi";

export default function ChatWindow({ group, user }) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [isAiTyping, setIsAiTyping] = useState(false);

  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages, isAiTyping]);

  useEffect(() => {
    if (!group) return;

    setMessages([]);
    setConnected(false);
    setIsAiTyping(false);

    const token = localStorage.getItem("token");
    if (!token) return;

    const userStr = localStorage.getItem("user");
    if (userStr) {
      const userData = JSON.parse(userStr);
      setCurrentUserId(userData.id);
    }

    const wsUrl = getWsUrl(group.id, token);
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "typing") {
        setIsAiTyping(true);
        return;
      }

      // When we get a consensus, stop typing
      if (msg.type === "consensus") {
        setIsAiTyping(false);
      }

      // Skip old-style system/agent messages that we no longer need individually
      if (msg.type === "user_joined" || msg.type === "user_left") {
        return;
      }

      setMessages((prev) => [...prev, msg]);
    };

    socket.onclose = () => {
      setConnected(false);
      setIsAiTyping(false);
    };

    socket.onerror = () => {
      setConnected(false);
    };

    return () => {
      socket.close();
    };
  }, [group?.id]);

  function sendMessage(text) {
    if (!socketRef.current) return;
    if (socketRef.current.readyState !== WebSocket.OPEN) return;
    socketRef.current.send(JSON.stringify({ message: text }));
  }

  return (
    <div
      data-testid="chat-window"
      className="flex-1 flex flex-col relative"
      style={{ background: "#0b141a" }}
    >
      {/* WhatsApp background pattern */}
      <div
        className="absolute inset-0 opacity-[0.08] pointer-events-none"
        style={{
          backgroundImage:
            "url('./bg-chat-tile-dark_a4be512e7195b6b733d9110b408f075d.png')",
          backgroundRepeat: "repeat",
        }}
      />

      <ChatHeader group={group} connected={connected} />

      {/* Messages */}
      <div
        data-testid="messages-container"
        className="flex-1 overflow-y-auto px-4 sm:px-8 py-4 space-y-2 relative z-10"
      >
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} currentUserId={currentUserId} />
        ))}

        {isAiTyping && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      <ChatInput sendMessage={sendMessage} disabled={!connected} />
    </div>
  );
}
