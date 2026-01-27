import { useState, useEffect, useRef } from 'react';
import { Search, MoreVertical, Smile, Paperclip, Send, Mic } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const WS_URL = BACKEND_URL.replace('http', 'ws');

export default function ChatWindow({ group, currentUser, onShowGroupInfo, availableAgents }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState([]);
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
    const { type, user_name, agent_name, agent_id, content, timestamp } = msg;

    // System messages
    if (type === 'user_joined' || type === 'user_left') {
      return (
        <div key={idx} className="flex justify-center my-2">
          <div className="bg-[#E9EDF2] px-3 py-1 rounded-md text-xs text-gray-600">
            {user_name} {type === 'user_joined' ? 'joined' : 'left'}
          </div>
        </div>
      );
    }

    // Consensus message
    if (type === 'consensus') {
      return (
        <div key={idx} className="flex justify-center my-4">
          <div className="bg-gradient-to-r from-purple-100 to-teal-100 px-6 py-3 rounded-lg shadow-sm max-w-2xl border border-purple-200">
            <div className="flex items-start gap-3">
              <div className="text-2xl">✨</div>
              <div>
                <div className="text-xs font-semibold text-purple-700 mb-1">CONSENSUS</div>
                <div className="text-sm text-gray-800">{content}</div>
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
        <div key={idx} className={`flex gap-2 mb-2 ${isCurrentUser ? 'justify-end' : 'justify-start'}`}>
          {!isCurrentUser && (
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-400 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0 mt-1">
              {user_name[0].toUpperCase()}
            </div>
          )}
          <div className={`max-w-md ${isCurrentUser ? 'items-end' : 'items-start'} flex flex-col`}>
            {!isCurrentUser && (
              <div className="text-xs text-gray-600 mb-1 px-2">{user_name}</div>
            )}
            <div className={`px-3 py-2 rounded-lg shadow-sm ${
              isCurrentUser 
                ? 'bg-[#E7D9F8] text-gray-800 rounded-br-none' 
                : 'bg-white text-gray-800 rounded-bl-none border border-gray-200'
            }`}>
              <div className="text-sm whitespace-pre-wrap break-words">{content}</div>
              <div className={`text-[10px] mt-1 ${
                isCurrentUser ? 'text-purple-600' : 'text-gray-500'
              } text-right`}>
                {formatTime(timestamp)}
              </div>
            </div>
          </div>
        </div>
      );
    }

    // Agent response
    if (type === 'agent_response') {
      const agentInfo = getAgentInfo(agent_id);
      
      return (
        <div key={idx} className="flex gap-2 mb-2 justify-start">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-teal-500 flex items-center justify-center text-white text-lg flex-shrink-0 mt-1">
            {agentInfo?.avatar || '🤖'}
          </div>
          <div className="max-w-md">
            <div className="text-xs text-purple-600 font-medium mb-1 px-2">{agent_name}</div>
            <div className="px-3 py-2 rounded-lg bg-gradient-to-br from-purple-50 to-teal-50 border border-purple-200 shadow-sm rounded-bl-none">
              <div className="text-sm text-gray-800 whitespace-pre-wrap break-words">{content}</div>
              <div className="text-[10px] text-purple-600 mt-1 text-right">
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
    <div className="flex-1 flex flex-col bg-[#F0F2F5]" data-testid="chat-window">
      {/* Header */}
      <div className="bg-[#F0F2F5] px-4 py-3 flex items-center justify-between border-b border-gray-200">
        <div 
          className="flex items-center gap-3 cursor-pointer hover:bg-gray-200 px-3 py-1 rounded-lg transition-colors"
          onClick={onShowGroupInfo}
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-teal-400 flex items-center justify-center text-white text-xl">
            {group.avatar || '💬'}
          </div>
          <div>
            <h2 className="font-medium text-gray-900">{group.name}</h2>
            <p className="text-xs text-gray-600">
              {isConnected ? (
                onlineUsers.length > 0 ? `${onlineUsers.length} online` : 'Connected'
              ) : (
                'Connecting...'
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="text-gray-600 hover:text-gray-800 transition-colors" title="Search">
            <Search size={20} />
          </button>
          <button className="text-gray-600 hover:text-gray-800 transition-colors" title="More">
            <MoreVertical size={20} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div 
        className="flex-1 overflow-y-auto px-8 py-4 bg-[#E5DDD5]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23d9d9d9' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
        }}
        data-testid="messages-container"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center bg-white/80 backdrop-blur-sm px-8 py-6 rounded-lg shadow-sm">
              <div className="text-4xl mb-4">💬</div>
              <p className="text-gray-600 font-medium mb-1">No messages yet</p>
              <p className="text-gray-500 text-sm">Send a message to start the conversation</p>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map(renderMessage)}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-[#F0F2F5] px-4 py-3">
        <div className="flex items-center gap-2">
          <button className="text-gray-600 hover:text-gray-800 transition-colors p-2 hover:bg-gray-200 rounded-full" title="Emoji">
            <Smile size={24} />
          </button>
          <button className="text-gray-600 hover:text-gray-800 transition-colors p-2 hover:bg-gray-200 rounded-full" title="Attach">
            <Paperclip size={24} />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message"
            className="flex-1 px-4 py-3 rounded-lg bg-white text-gray-800 placeholder-gray-500 outline-none focus:outline-none border border-gray-200"
            disabled={!isConnected}
            data-testid="message-input"
          />
          {input.trim() ? (
            <button
              onClick={sendMessage}
              disabled={!isConnected}
              className="bg-gradient-to-r from-purple-500 to-teal-500 text-white p-3 rounded-full hover:from-purple-600 hover:to-teal-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
              data-testid="send-button"
            >
              <Send size={20} />
            </button>
          ) : (
            <button className="text-gray-600 hover:text-gray-800 transition-colors p-3 hover:bg-gray-200 rounded-full" title="Voice">
              <Mic size={24} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}