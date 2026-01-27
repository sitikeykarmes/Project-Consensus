import { useEffect, useRef, useState } from "react";
import Sidebar from "../components/Sidebar";
import TopBar from "../components/TopBar";
import ChatWindow from "../components/ChatWindow";

export default function ChatRoom() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  const roomId = "room1";
  const userName = "Kartikey";

  // AI Agents list
  const agents = ["Research Agent", "Analysis Agent", "Synthesis Agent"];

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8001/ws/${roomId}/${userName}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("✅ Connected to WebSocket");
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Handle user joined/left to update online users
      if (data.type === "user_joined") {
        setOnlineUsers(prev => [...new Set([...prev, data.user_name])]);
      }
      if (data.type === "user_left") {
        setOnlineUsers(prev => prev.filter(u => u !== data.user_name));
      }

      setMessages((prev) => [...prev, data]);
    };

    ws.onclose = () => {
      console.log("❌ WebSocket disconnected");
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
    };

    return () => ws.close();
  }, []);

  const sendMessage = () => {
    if (!input.trim() || !isConnected) return;

    wsRef.current.send(
      JSON.stringify({
        message: input,
      }),
    );

    setInput("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-slate-900 text-white" data-testid="chat-room">
      {/* Sidebar */}
      <Sidebar users={onlineUsers} agents={agents} currentUser={userName} />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <TopBar roomName="Project Consensus Chat" isConnected={isConnected} onlineCount={onlineUsers.length} />

        {/* Chat Messages */}
        <ChatWindow messages={messages} currentUser={userName} messagesEndRef={messagesEndRef} />

        {/* Input Box */}
        <div className="bg-slate-800 border-t border-slate-700 p-4">
          <div className="flex gap-3 max-w-6xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 px-4 py-3 rounded-lg bg-slate-700 text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              disabled={!isConnected}
              data-testid="message-input"
            />
            <button
              onClick={sendMessage}
              disabled={!isConnected || !input.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-lg font-semibold transition-all transform hover:scale-105 active:scale-95"
              data-testid="send-button"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
