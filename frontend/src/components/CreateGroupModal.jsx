import { useState } from 'react';
import { X, Sparkles } from 'lucide-react';

const EMOJI_OPTIONS = ['💬', '👥', '💡', '🎉', '🚀', '⭐', '🌈', '🎯', '💥', '🎓', '💻', '🎨', '🌎', '🔥', '✨', '🌟'];

export default function CreateGroupModal({ onClose, onCreate, availableAgents }) {
  const [groupName, setGroupName] = useState('');
  const [selectedAvatar, setSelectedAvatar] = useState('💬');
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [isCreating, setIsCreating] = useState(false);

  const handleToggleAgent = (agentId) => {
    if (selectedAgents.includes(agentId)) {
      setSelectedAgents(selectedAgents.filter(id => id !== agentId));
    } else {
      setSelectedAgents([...selectedAgents, agentId]);
    }
  };

  const handleCreate = async () => {
    if (!groupName.trim()) return;
    
    setIsCreating(true);
    await onCreate({
      name: groupName,
      avatar: selectedAvatar,
      members: [],
      agents: selectedAgents
    });
    setIsCreating(false);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 animate-fadeIn" onClick={onClose}>
      <div 
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden transform scale-100 animate-slideIn"
        onClick={(e) => e.stopPropagation()}
        data-testid="create-group-modal"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 via-purple-600 to-indigo-600 px-7 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="text-white" size={24} />
            <h2 className="text-xl font-bold text-white">Create New Group</h2>
          </div>
          <button 
            onClick={onClose}
            className="text-white hover:bg-white/20 p-2 rounded-full transition-all duration-200"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-7 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Group Name */}
          <div>
            <label className="block text-sm font-semibold text-gray-800 mb-2">
              Group Name *
            </label>
            <input
              type="text"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              placeholder="Enter group name"
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 text-gray-800 placeholder-gray-400"
              autoFocus
              data-testid="group-name-input"
            />
          </div>

          {/* Avatar Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-800 mb-3">
              Choose Avatar
            </label>
            <div className="grid grid-cols-8 gap-2">
              {EMOJI_OPTIONS.map((emoji) => (
                <button
                  key={emoji}
                  onClick={() => setSelectedAvatar(emoji)}
                  className={`text-3xl p-3 rounded-xl transition-all duration-200 ${
                    selectedAvatar === emoji 
                      ? 'bg-gradient-to-br from-purple-100 to-indigo-100 ring-4 ring-purple-400 shadow-lg transform scale-110' 
                      : 'bg-gray-100 hover:bg-gray-200 hover:scale-105'
                  }`}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>

          {/* AI Agents Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-800 mb-3">
              Add AI Agents (Optional)
            </label>
            <div className="space-y-2.5 max-h-56 overflow-y-auto pr-2">
              {availableAgents.map((agent) => {
                const isSelected = selectedAgents.includes(agent.id);
                return (
                  <div
                    key={agent.id}
                    onClick={() => handleToggleAgent(agent.id)}
                    className={`flex items-center gap-4 p-4 rounded-xl cursor-pointer transition-all duration-200 border-2 ${
                      isSelected
                        ? 'bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-400 shadow-md transform scale-[1.02]'
                        : 'bg-gray-50 border-gray-200 hover:border-purple-300 hover:bg-gray-100 hover:shadow-sm'
                    }`}
                    data-testid={`agent-option-${agent.id}`}
                  >
                    <div className={`text-3xl transform transition-transform duration-200 ${
                      isSelected ? 'scale-110' : ''
                    }`}>
                      {agent.avatar}
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 text-base">{agent.name}</div>
                      <div className="text-xs text-purple-600 font-medium">🤖 AI Assistant</div>
                    </div>
                    {isSelected && (
                      <div className="w-7 h-7 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center shadow-md">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            {selectedAgents.length > 0 && (
              <p className="text-xs text-purple-600 mt-3 font-medium">
                ✨ {selectedAgents.length} agent{selectedAgents.length > 1 ? 's' : ''} selected
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-7 py-5 bg-gradient-to-b from-gray-50 to-gray-100 flex gap-3 justify-end border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl text-gray-700 font-semibold hover:bg-white transition-all duration-200 border-2 border-gray-300 hover:border-gray-400"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={!groupName.trim() || isCreating}
            className="px-6 py-2.5 bg-gradient-to-r from-purple-500 via-purple-600 to-indigo-600 text-white rounded-xl hover:from-purple-600 hover:via-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold shadow-md hover:shadow-lg transform hover:scale-105 active:scale-95 flex items-center gap-2"
            data-testid="create-group-submit"
          >
            {isCreating ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              </>
            ) : (
              <>
                <Sparkles size={18} />
                Create Group
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}