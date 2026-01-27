import { useState } from 'react';
import { X } from 'lucide-react';

const EMOJI_OPTIONS = ['💬', '👥', '💡', '🎉', '🚀', '⭐', '🌈', '🎯', '💥', '🎓', '💻', '🎨'];

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
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-white rounded-lg shadow-2xl w-full max-w-md mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        data-testid="create-group-modal"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-teal-500 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Create New Group</h2>
          <button 
            onClick={onClose}
            className="text-white hover:bg-white/20 p-1 rounded-full transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Group Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Group Name
            </label>
            <input
              type="text"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              placeholder="Enter group name"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              autoFocus
              data-testid="group-name-input"
            />
          </div>

          {/* Avatar Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Choose Avatar
            </label>
            <div className="grid grid-cols-6 gap-2">
              {EMOJI_OPTIONS.map((emoji) => (
                <button
                  key={emoji}
                  onClick={() => setSelectedAvatar(emoji)}
                  className={`text-3xl p-3 rounded-lg transition-all hover:scale-110 ${
                    selectedAvatar === emoji 
                      ? 'bg-gradient-to-br from-purple-100 to-teal-100 ring-2 ring-purple-500 shadow-md' 
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>

          {/* AI Agents Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Add AI Agents (Optional)
            </label>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {availableAgents.map((agent) => (
                <div
                  key={agent.id}
                  onClick={() => handleToggleAgent(agent.id)}
                  className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all border-2 ${
                    selectedAgents.includes(agent.id)
                      ? 'bg-gradient-to-r from-purple-50 to-teal-50 border-purple-400 shadow-sm'
                      : 'bg-gray-50 border-gray-200 hover:border-gray-300 hover:bg-gray-100'
                  }`}
                  data-testid={`agent-option-${agent.id}`}
                >
                  <div className="text-2xl">{agent.avatar}</div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="text-xs text-gray-600">AI Assistant</div>
                  </div>
                  {selectedAgents.includes(agent.id) && (
                    <div className="w-5 h-5 bg-gradient-to-r from-purple-500 to-teal-500 rounded-full flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-lg text-gray-700 hover:bg-gray-200 transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={!groupName.trim() || isCreating}
            className="px-6 py-2.5 bg-gradient-to-r from-purple-500 to-teal-500 text-white rounded-lg hover:from-purple-600 hover:to-teal-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-md"
            data-testid="create-group-submit"
          >
            {isCreating ? 'Creating...' : 'Create Group'}
          </button>
        </div>
      </div>
    </div>
  );
}