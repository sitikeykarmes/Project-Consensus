import { useState, useEffect, useRef } from 'react';
import { Search, MoreVertical, Smile, Paperclip, Send, Mic, Phone, Video } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const WS_URL = BACKEND_URL.replace('http', 'ws');

export default function ChatWindow({ group, currentUser, onShowGroupInfo, availableAgents }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Reset messages when group changes
    setMessages([]);
    
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`${WS_URL}/ws/${group.id}/${currentUser}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'user_joined' || data.type === 'user_left') {
        setOnlineUsers(data.online_users || []);
      }
      
      // Show typing indicator for agent responses
      if (data.type === 'agent_response' || data.type === 'consensus') {
        setIsTyping(false);
      }
      
      setMessages((prev) => [...prev, data]);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    return () => ws.close();
  }, [group.id, currentUser]);

  const sendMessage = () => {
    if (!input.trim() || !isConnected) return;

    // Show typing indicator if agents are present
    if (group.agents && group.agents.length > 0) {
      setIsTyping(true);
    }

    wsRef.current.send(
      JSON.stringify({
        message: input,
      }),
    );

    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
  };

  const getAgentInfo = (agentId) => {
    return availableAgents.find(a => a.id === agentId);
  };

  const renderMessage = (msg, idx) => {
    const { type, user_name, agent_name, agent_id, content, timestamp, mode_used } = msg;

    // System messages
    if (type === 'user_joined' || type === 'user_left') {
      return (
        <div key={idx} className="flex justify-center my-3">
          <div className="bg-white/90 backdrop-blur-sm shadow-sm px-4 py-2 rounded-full text-xs text-gray-700 font-medium border border-gray-200">
            <span className="inline-flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              {user_name} {type === 'user_joined' ? 'joined the chat' : 'left the chat'}
            </span>
          </div>
        </div>
      );
    }

    // Consensus message
    if (type === 'consensus') {
      return (
        <div key={idx} className="flex justify-center my-6 px-4">
          <div className="bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 px-6 py-4 rounded-2xl shadow-lg max-w-3xl border-2 border-emerald-200 transform hover:scale-[1.02] transition-transform duration-200">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center shadow-md">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider bg-emerald-100 px-2 py-1 rounded-full">✨ Final Consensus</span>
                  {mode_used && (
                    <span className="text-xs text-teal-600 bg-teal-50 px-2 py-1 rounded-full font-medium">
                      Mode: {mode_used}
                    </span>
                  )}
                </div>
                <div className="text-sm leading-relaxed text-gray-800 font-medium whitespace-pre-wrap break-words">{content}</div>
                <div className="text-[10px] text-emerald-600 mt-2 font-medium">{formatTime(timestamp)}</div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // User message
    if (type === 'user_message') {
      const isCurrentUser = user_name === currentUser;
      
      return (
        <div key={idx} className={`flex gap-2 mb-3 px-4 animate-fadeIn ${isCurrentUser ? 'justify-end' : 'justify-start'}`}>
          {!isCurrentUser && (
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white text-sm font-bold flex-shrink-0 mt-1 shadow-md ring-2 ring-white">
              {user_name[0].toUpperCase()}
            </div>
          )}
          <div className={`max-w-md ${isCurrentUser ? 'items-end' : 'items-start'} flex flex-col`}>
            {!isCurrentUser && (
              <div className="text-xs font-semibold text-gray-700 mb-1 px-3">{user_name}</div>
            )}
            <div className={`px-4 py-2.5 rounded-2xl shadow-md transform hover:scale-[1.02] transition-all duration-200 ${
              isCurrentUser 
                ? 'bg-gradient-to-br from-purple-500 to-indigo-600 text-white rounded-br-md' 
                : 'bg-white text-gray-800 rounded-bl-md border border-gray-200'
            }`}>
              <div className="text-sm whitespace-pre-wrap break-words leading-relaxed">{content}</div>
              <div className={`text-[10px] mt-1.5 ${
                isCurrentUser ? 'text-purple-100' : 'text-gray-500'
              } text-right font-medium`}>
                {formatTime(timestamp)}
              </div>
            </div>
          </div>
          {isCurrentUser && (
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-500 flex items-center justify-center text-white text-sm font-bold flex-shrink-0 mt-1 shadow-md ring-2 ring-white">
              {user_name[0].toUpperCase()}
            </div>
          )}
        </div>
      );
    }

    // Agent response
    if (type === 'agent_response') {
      const agentInfo = getAgentInfo(agent_id);
      
      return (
        <div key={idx} className="flex gap-2 mb-3 px-4 justify-start animate-fadeIn">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 flex items-center justify-center text-white text-xl flex-shrink-0 mt-1 shadow-lg ring-2 ring-white animate-pulse-slow">
            {agentInfo?.avatar || '🤖'}
          </div>
          <div className="max-w-2xl">
            <div className="flex items-center gap-2 mb-1 px-3">
              <span className="text-xs text-purple-700 font-bold">{agent_name}</span>
              <span className="text-[10px] text-purple-500 bg-purple-50 px-2 py-0.5 rounded-full font-semibold">AI Agent</span>
            </div>
            <div className="px-4 py-3 rounded-2xl bg-gradient-to-br from-purple-50 via-violet-50 to-fuchsia-50 border-2 border-purple-200 shadow-lg rounded-bl-md transform hover:scale-[1.01] transition-all duration-200">
              <div className="text-sm text-gray-800 whitespace-pre-wrap break-words leading-relaxed font-medium">{content}</div>
              <div className="text-[10px] text-purple-600 mt-2 text-right font-semibold">
                {formatTime(timestamp)}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="flex-1 flex flex-col bg-gradient-to-b from-gray-50 to-gray-100" data-testid="chat-window">
      {/* Header */}
      <div className="bg-white px-5 py-3.5 flex items-center justify-between border-b border-gray-200 shadow-sm">
        <div 
          className="flex items-center gap-3 cursor-pointer hover:bg-gray-50 px-3 py-2 rounded-xl transition-all duration-200 group"
          onClick={onShowGroupInfo}
        >
          <div className="relative">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 via-pink-400 to-red-400 flex items-center justify-center text-white text-2xl shadow-md group-hover:shadow-lg transition-shadow duration-200">
              {group.avatar || '💬'}
            </div>
            {isConnected && (
              <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white shadow-sm"></div>
            )}
          </div>
          <div>
            <h2 className="font-semibold text-gray-900 text-base">{group.name}</h2>
            <p className="text-xs text-gray-600 font-medium">
              {isConnected ? (
                onlineUsers.length > 0 ? (
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    {onlineUsers.length} online
                  </span>
                ) : 'Connected'
              ) : (
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                  Connecting...
                </span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 p-2.5 rounded-full transition-all duration-200" title="Video call">
            <Video size={20} />
          </button>
          <button className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 p-2.5 rounded-full transition-all duration-200" title="Voice call">
            <Phone size={20} />
          </button>
          <button className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 p-2.5 rounded-full transition-all duration-200" title="Search">
            <Search size={20} />
          </button>
          <button className="text-gray-600 hover:text-gray-900 hover:bg-gray-100 p-2.5 rounded-full transition-all duration-200" title="More">
            <MoreVertical size={20} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div 
        className="flex-1 overflow-y-auto py-4"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%239C92AC' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          backgroundColor: '#F0F2F5'
        }}
        data-testid="messages-container"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center bg-white/95 backdrop-blur-md px-10 py-8 rounded-2xl shadow-xl border border-gray-200">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center">
                <span className="text-5xl">💬</span>
              </div>
              <p className="text-gray-800 font-semibold mb-2 text-lg">No messages yet</p>
              <p className="text-gray-600 text-sm">Send a message to start the conversation</p>
              {group.agents && group.agents.length > 0 && (
                <p className="text-purple-600 text-xs mt-3 font-medium">🤖 {group.agents.length} AI agent(s) ready to assist</p>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map(renderMessage)}
            {isTyping && (
              <div className="flex gap-2 mb-3 px-4 justify-start">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white text-xl flex-shrink-0 mt-1 shadow-lg">
                  🤖
                </div>
                <div className="bg-white px-5 py-3 rounded-2xl shadow-md border border-gray-200">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-white px-5 py-3 border-t border-gray-200 shadow-lg">
        <div className="flex items-center gap-3">
          <button className="text-gray-600 hover:text-purple-600 hover:bg-purple-50 transition-all duration-200 p-2.5 rounded-full" title="Emoji">
            <Smile size={24} />
          </button>
          <button className="text-gray-600 hover:text-purple-600 hover:bg-purple-50 transition-all duration-200 p-2.5 rounded-full" title="Attach">
            <Paperclip size={24} />
          </button>
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message"
              className="w-full px-5 py-3 rounded-full bg-gray-100 text-gray-800 placeholder-gray-500 outline-none focus:outline-none focus:bg-white focus:ring-2 focus:ring-purple-300 border border-transparent focus:border-purple-300 transition-all duration-200 text-sm"
              disabled={!isConnected}
              data-testid="message-input"
            />
          </div>
          {input.trim() ? (
            <button
              onClick={sendMessage}
              disabled={!isConnected}
              className="bg-gradient-to-r from-purple-500 via-purple-600 to-indigo-600 text-white p-3.5 rounded-full hover:from-purple-600 hover:via-purple-700 hover:to-indigo-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95"
              data-testid="send-button"
            >
              <Send size={20} />
            </button>
          ) : (
            <button className="text-gray-600 hover:text-purple-600 hover:bg-purple-50 transition-all duration-200 p-3 rounded-full" title="Voice message">
              <Mic size={24} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}