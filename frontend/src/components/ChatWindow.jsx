import { useEffect, useRef, useState } from "react";
import ChatHeader from "./ChatHeader";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import ChatInput from "./ChatInput";
import { getWsUrl, markGroupRead } from "../api/chatApi";

export default function ChatWindow({ group, user, onGroupDeleted }) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [typingStatus, setTypingStatus] = useState("AI is thinking...");
  const [streamingMsg, setStreamingMsg] = useState(null);

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

    // Automatically mark the current room as Read to suppress badges
    markGroupRead(group.id, token);

    const userStr = localStorage.getItem("user");
    if (userStr) {
      const userData = JSON.parse(userStr);
      setCurrentUserId(userData.id);
    }

    const wsUrl = getWsUrl(group.id, token);
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "typing") {
        setIsAiTyping(true);
        if (msg.status_message) {
          setTypingStatus(msg.status_message);
        } else {
          setTypingStatus("AI is thinking...");
        }
        return;
      }

      if (msg.type === "user_joined" || msg.type === "user_left") return;

      if (msg.type === "consensus_stream") {
        setStreamingMsg((prev) => {
          if (!prev) {
            return {
              type: "consensus",
              sender_name: "Consensus Synthesis Agent",
              content: msg.content,
              timestamp: new Date().toISOString(),
              agent_responses: [], // Kept blank until final consensus payload drops
              _streaming: true
            };
          }
          return {
            ...prev,
            content: prev.content + msg.content,
          };
        });
        return;
      }

      if (msg.type === "consensus") {
        setIsAiTyping(false);
        setStreamingMsg(null); // Drop the active stream buffer 
        if (!msg.historical) markGroupRead(group.id, token);
      }

      if (msg.type === "user") {
        if (!msg.historical) markGroupRead(group.id, token);
        setMessages((prev) => {
          const optimisticIndex = prev.findLastIndex(
            (m) => m._optimistic && m.content === msg.content,
          );
          if (optimisticIndex !== -1) {
            const updated = [...prev];
            updated[optimisticIndex] = msg;
            return updated;
          }
          return [...prev, msg];
        });
        return;
      }

      setMessages((prev) => [...prev, msg]);
    };

    socket.onclose = () => {
      setConnected(false);
      setIsAiTyping(false);
    };

    socket.onerror = () => setConnected(false);

    return () => socket.close();
  }, [group?.id]);

  function sendMessage(text) {
    if (!socketRef.current) return;
    if (socketRef.current.readyState !== WebSocket.OPEN) return;

    const userStr = localStorage.getItem("user");
    const userData = userStr ? JSON.parse(userStr) : {};

    const optimisticMsg = {
      type: "user",
      sender_id: userData.id || currentUserId,
      sender_name: userData.email || "You",
      content: text,
      timestamp: new Date().toISOString(),
      _optimistic: true,
    };

    setMessages((prev) => [...prev, optimisticMsg]);
    socketRef.current.send(JSON.stringify({ message: text }));
  }

  function handleGroupDeleted() {
    socketRef.current?.close();
    onGroupDeleted?.(group.id);
  }

  return (
    <div
      data-testid="chat-window"
      className="flex-1 flex flex-col relative"
      style={{ background: "#0b141a" }}
    >
      <div
        className="absolute inset-0 opacity-[0.08] pointer-events-none"
        style={{
          backgroundImage:
            "url('./bg-chat-tile-dark_a4be512e7195b6b733d9110b408f075d.png')",
          backgroundRepeat: "repeat",
        }}
      />

      <ChatHeader
        group={group}
        connected={connected}
        onGroupDeleted={handleGroupDeleted}
      />

      <div
        data-testid="messages-container"
        className="flex-1 overflow-y-auto px-4 sm:px-8 py-4 space-y-2 relative z-10"
      >
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} currentUserId={currentUserId} />
        ))}
        {streamingMsg && <MessageBubble msg={streamingMsg} currentUserId={currentUserId} />}
        {isAiTyping && !streamingMsg && <TypingIndicator status={typingStatus} />}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput sendMessage={sendMessage} disabled={!connected} />
    </div>
  );
}
