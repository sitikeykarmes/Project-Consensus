export default function Sidebar({ users, agents, currentUser }) {
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
    const index = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length;
    return colors[index];
  };

  const getInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col" data-testid="sidebar">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-700">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
          </svg>
          Group Chat
        </h2>
      </div>

      {/* Users Section */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Online - {users.length}
          </h3>
          <div className="space-y-2">
            {users.length === 0 ? (
              <div className="text-sm text-slate-500 italic">No users online</div>
            ) : (
              users.map((user, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-700 transition-colors cursor-pointer"
                  data-testid={`user-${user}`}
                >
                  <div className="relative">
                    <div className={`w-10 h-10 rounded-full ${getAvatarColor(user)} flex items-center justify-center font-semibold text-white`}>
                      {getInitials(user)}
                    </div>
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-slate-800 rounded-full"></div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white truncate">
                      {user}
                      {user === currentUser && (
                        <span className="ml-1 text-xs text-slate-400">(You)</span>
                      )}
                    </div>
                    <div className="text-xs text-green-500">Online</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* AI Agents Section */}
        <div className="p-4 border-t border-slate-700">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            AI Agents
          </h3>
          <div className="space-y-2">
            {agents.map((agent, i) => (
              <div
                key={i}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-700 transition-colors"
                data-testid={`agent-${agent}`}
              >
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-purple-300 truncate">{agent}</div>
                  <div className="text-xs text-slate-400">AI Assistant</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
