import { Search, MessageCircle, MoreVertical, Plus, Users } from 'lucide-react';

export default function Sidebar({ groups, selectedGroup, onGroupSelect, onCreateGroup, currentUser }) {
  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div className="w-[420px] flex flex-col bg-white border-r border-gray-200 shadow-lg" data-testid="sidebar">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500 via-purple-600 to-indigo-600 px-5 py-4 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <div className="relative group">
            <div className="w-11 h-11 rounded-full bg-gradient-to-br from-white to-gray-100 flex items-center justify-center text-purple-600 font-bold text-lg shadow-md ring-2 ring-white/50 group-hover:ring-white transition-all duration-200">
              {currentUser[0].toUpperCase()}
            </div>
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-white shadow-sm"></div>
          </div>
          <div>
            <span className="font-semibold text-white text-base">{currentUser}</span>
            <p className="text-xs text-purple-100 font-medium">Active now</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="text-white hover:bg-white/20 transition-all duration-200 p-2 rounded-full" title="New Chat">
            <MessageCircle size={20} />
          </button>
          <button className="text-white hover:bg-white/20 transition-all duration-200 p-2 rounded-full" title="Menu">
            <MoreVertical size={20} />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="px-4 py-3 bg-gradient-to-b from-gray-50 to-white border-b border-gray-200">
        <div className="bg-white rounded-xl px-4 py-2.5 flex items-center gap-3 shadow-sm border border-gray-200 focus-within:border-purple-300 focus-within:ring-2 focus-within:ring-purple-100 transition-all duration-200">
          <Search size={18} className="text-gray-400" />
          <input 
            type="text" 
            placeholder="Search or start new chat"
            className="bg-transparent flex-1 outline-none text-sm text-gray-700 placeholder-gray-400"
          />
        </div>
      </div>

      {/* Create Group Button */}
      <div className="px-4 py-3 bg-white border-b border-gray-200">
        <button
          onClick={onCreateGroup}
          className="w-full bg-gradient-to-r from-purple-500 via-purple-600 to-indigo-600 text-white px-4 py-3 rounded-xl font-semibold hover:from-purple-600 hover:via-purple-700 hover:to-indigo-700 transition-all duration-200 flex items-center justify-center gap-2 shadow-md hover:shadow-lg transform hover:scale-[1.02] active:scale-[0.98]"
          data-testid="create-group-button"
        >
          <Plus size={20} strokeWidth={2.5} />
          Create New Group
        </button>
      </div>

      {/* Groups List */}
      <div className="flex-1 overflow-y-auto bg-white" data-testid="groups-list">
        {groups.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-8 py-12">
            <div className="w-28 h-28 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-full flex items-center justify-center mb-5 shadow-md">
              <Users size={48} className="text-purple-500" />
            </div>
            <p className="text-gray-800 font-semibold mb-2 text-lg">No groups yet</p>
            <p className="text-gray-600 text-sm leading-relaxed max-w-xs">Create your first group and start collaborating with AI agents</p>
          </div>
        ) : (
          groups.map((group) => {
            const isSelected = selectedGroup?.id === group.id;
            return (
              <div
                key={group.id}
                onClick={() => onGroupSelect(group)}
                className={`px-4 py-3.5 flex items-center gap-3 cursor-pointer transition-all duration-200 border-b border-gray-100 relative ${
                  isSelected 
                    ? 'bg-gradient-to-r from-purple-50 to-indigo-50 border-l-4 border-l-purple-500' 
                    : 'hover:bg-gray-50 border-l-4 border-l-transparent'
                }`}
                data-testid={`group-${group.id}`}
              >
                {/* Avatar */}
                <div className="relative flex-shrink-0">
                  <div className={`w-14 h-14 rounded-full bg-gradient-to-br from-purple-400 via-pink-400 to-red-400 flex items-center justify-center text-white text-2xl shadow-md ${
                    isSelected ? 'ring-4 ring-purple-200' : ''
                  } transform transition-transform duration-200 hover:scale-105`}>
                    {group.avatar || '💬'}
                  </div>
                  {group.agents && group.agents.length > 0 && (
                    <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md border-2 border-white">
                      {group.agents.length}
                    </div>
                  )}
                </div>

                {/* Group Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className={`font-semibold truncate ${
                      isSelected ? 'text-purple-700' : 'text-gray-900'
                    }`}>
                      {group.name}
                    </h3>
                    <span className={`text-[11px] ml-2 flex-shrink-0 font-medium ${
                      isSelected ? 'text-purple-600' : 'text-gray-500'
                    }`}>
                      {formatTime(group.last_message_time)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <p className={`text-sm truncate ${
                      isSelected ? 'text-purple-600' : 'text-gray-600'
                    }`}>
                      {group.last_message || 'No messages yet'}
                    </p>
                  </div>
                  {group.agents && group.agents.length > 0 && (
                    <div className="mt-1.5 flex items-center gap-1">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r from-purple-100 to-fuchsia-100 text-purple-700 border border-purple-200">
                        🤖 {group.agents.length} AI Agent{group.agents.length > 1 ? 's' : ''}
                      </span>
                    </div>
                  )}
                </div>

                {/* Unread indicator (can be added dynamically) */}
                {isSelected && (
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-purple-500 to-indigo-500 rounded-full"></div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}