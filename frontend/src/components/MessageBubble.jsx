export default function MessageBubble({ message, currentUser }) {
  const { type, user_name, agent_name, content, timestamp } = message;

  // Generate avatar color based on name
  const getAvatarColor = (name) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-indigo-500',
      'bg-teal-500'
    ];
    const index = name?.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length;
    return colors[index];
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  // System messages (user joined/left)
  if (type === "user_joined" || type === "user_left") {
    return (
      <div className="flex justify-center my-2" data-testid="system-message">
        <div className="bg-slate-800 px-4 py-2 rounded-full text-xs text-slate-400 flex items-center gap-2">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
          </svg>
          <span>
            {user_name} {type === "user_joined" ? "joined the chat" : "left the chat"}
          </span>
        </div>
      </div>
    );
  }

  // Consensus message
  if (type === "consensus") {
    return (
      <div className="flex justify-center my-4" data-testid="consensus-message">
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 px-6 py-3 rounded-lg shadow-lg max-w-2xl">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-xs font-semibold text-white/90 mb-1 uppercase tracking-wide">Consensus Reached</div>
              <div className="text-sm text-white font-medium">{content}</div>
              {timestamp && <div className="text-xs text-white/70 mt-2">{formatTime(timestamp)}</div>}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // User message
  if (type === "user_message") {
    const isCurrentUser = user_name === currentUser;
    
    return (
      <div className={`flex gap-3 ${isCurrentUser ? 'flex-row-reverse' : 'flex-row'}`} data-testid="user-message">
        {/* Avatar */}
        {!isCurrentUser && (
          <div className={`w-10 h-10 rounded-full ${getAvatarColor(user_name)} flex items-center justify-center font-semibold text-white flex-shrink-0`}>
            {getInitials(user_name)}
          </div>
        )}

        {/* Message Content */}
        <div className={`flex flex-col max-w-xl ${isCurrentUser ? 'items-end' : 'items-start'}`}>
          {!isCurrentUser && (
            <div className="text-xs font-medium text-slate-400 mb-1 px-1">{user_name}</div>
          )}
          <div className={`px-4 py-2 rounded-2xl ${
            isCurrentUser 
              ? 'bg-blue-600 text-white rounded-br-sm' 
              : 'bg-slate-700 text-white rounded-bl-sm'
          }`}>
            <div className="text-sm whitespace-pre-wrap break-words">{content}</div>
          </div>
          {timestamp && (
            <div className="text-xs text-slate-500 mt-1 px-1">{formatTime(timestamp)}</div>
          )}
        </div>

        {/* Current user avatar on right */}
        {isCurrentUser && (
          <div className={`w-10 h-10 rounded-full ${getAvatarColor(user_name)} flex items-center justify-center font-semibold text-white flex-shrink-0`}>
            {getInitials(user_name)}
          </div>
        )}
      </div>
    );
  }

  // Agent response
  if (type === "agent_response") {
    return (
      <div className="flex gap-3" data-testid="agent-message">
        {/* Agent Avatar */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center flex-shrink-0">
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </div>

        {/* Message Content */}
        <div className="flex flex-col max-w-xl">
          <div className="text-xs font-medium text-purple-400 mb-1 px-1 flex items-center gap-2">
            <span>{agent_name}</span>
            <span className="text-slate-500">• AI Assistant</span>
          </div>
          <div className="px-4 py-2 rounded-2xl bg-slate-700 text-white rounded-bl-sm border border-purple-500/30">
            <div className="text-sm whitespace-pre-wrap break-words">{content}</div>
          </div>
          {timestamp && (
            <div className="text-xs text-slate-500 mt-1 px-1">{formatTime(timestamp)}</div>
          )}
        </div>
      </div>
    );
  }

  return null;
}
