import { Search, MessageCircle, MoreVertical, Plus } from 'lucide-react';

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
    <div className="w-[420px] flex flex-col bg-white border-r border-gray-200" data-testid="sidebar">
      {/* Header */}
      <div className="bg-[#F0F2F5] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-teal-400 flex items-center justify-center text-white font-semibold">
            {currentUser[0].toUpperCase()}
          </div>
          <span className="font-medium text-gray-800">{currentUser}</span>
        </div>
        <div className="flex items-center gap-4">
          <button className="text-gray-600 hover:text-gray-800 transition-colors" title="New Chat">
            <MessageCircle size={20} />
          </button>
          <button className="text-gray-600 hover:text-gray-800 transition-colors" title="Menu">
            <MoreVertical size={20} />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="px-3 py-2 bg-white border-b border-gray-200">
        <div className="bg-[#F0F2F5] rounded-lg px-4 py-2 flex items-center gap-3">
          <Search size={18} className="text-gray-500" />
          <input 
            type="text" 
            placeholder="Search or start new chat"
            className="bg-transparent flex-1 outline-none text-sm text-gray-700 placeholder-gray-500"
          />
        </div>
      </div>

      {/* Create Group Button */}
      <div className="px-3 py-2 bg-white border-b border-gray-200">
        <button
          onClick={onCreateGroup}
          className="w-full bg-gradient-to-r from-purple-500 to-teal-500 text-white px-4 py-2.5 rounded-lg font-medium hover:from-purple-600 hover:to-teal-600 transition-all flex items-center justify-center gap-2 shadow-md"
          data-testid="create-group-button"
        >
          <Plus size={18} />
          Create New Group
        </button>
      </div>

      {/* Groups List */}
      <div className="flex-1 overflow-y-auto bg-white" data-testid="groups-list">
        {groups.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-8 py-12">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <MessageCircle size={40} className="text-gray-400" />
            </div>
            <p className="text-gray-600 font-medium mb-2">No groups yet</p>
            <p className="text-gray-500 text-sm">Create a group to start chatting</p>
          </div>
        ) : (
          groups.map((group) => (
            <div
              key={group.id}
              onClick={() => onGroupSelect(group)}
              className={`px-4 py-3 flex items-center gap-3 cursor-pointer transition-all border-b border-gray-100 hover:bg-[#F5F5F5] ${
                selectedGroup?.id === group.id ? 'bg-[#F0F2F5]' : ''
              }`}
              data-testid={`group-${group.id}`}
            >
              {/* Avatar */}
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-teal-400 flex items-center justify-center text-white text-xl flex-shrink-0">
                {group.avatar || '💬'}
              </div>

              {/* Group Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-medium text-gray-900 truncate">{group.name}</h3>
                  <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
                    {formatTime(group.last_message_time)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600 truncate">
                    {group.last_message || 'No messages yet'}
                  </p>
                  {group.agents && group.agents.length > 0 && (
                    <div className="ml-2 flex-shrink-0">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                        🤖 {group.agents.length}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}