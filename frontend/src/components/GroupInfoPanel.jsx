import { X, UserPlus, Users } from 'lucide-react';
import { useState } from 'react';

export default function GroupInfoPanel({ group, onClose, availableAgents, onAddMember, onRefresh }) {
  const [showAddMember, setShowAddMember] = useState(false);
  const [newMemberName, setNewMemberName] = useState('');

  const handleAddUser = async () => {
    if (!newMemberName.trim()) return;
    await onAddMember(group.id, newMemberName, 'user');
    setNewMemberName('');
    setShowAddMember(false);
    onRefresh();
  };

  const handleAddAgent = async (agentId) => {
    await onAddMember(group.id, agentId, 'agent');
    onRefresh();
  };

  const getAgentInfo = (agentId) => {
    return availableAgents.find(a => a.id === agentId);
  };

  const groupAgents = group.agents?.map(getAgentInfo).filter(Boolean) || [];

  return (
    <div className="absolute right-0 top-0 bottom-0 w-96 bg-white shadow-2xl z-10 flex flex-col border-l border-gray-200" data-testid="group-info-panel">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500 to-teal-500 px-6 py-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Group Info</h2>
        <button 
          onClick={onClose}
          className="text-white hover:bg-white/20 p-1 rounded-full transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Group Avatar & Name */}
        <div className="px-6 py-8 text-center bg-gradient-to-b from-purple-50 to-white">
          <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-purple-400 to-teal-400 flex items-center justify-center text-white text-5xl mb-4 shadow-lg">
            {group.avatar || '💬'}
          </div>
          <h3 className="text-xl font-semibold text-gray-900">{group.name}</h3>
          <p className="text-sm text-gray-600 mt-1">Group • {group.members?.length || 0} members</p>
        </div>

        {/* Members Section */}
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-gray-700 font-medium">
              <Users size={20} />
              <span>Members</span>
            </div>
            <button
              onClick={() => setShowAddMember(!showAddMember)}
              className="text-purple-600 hover:text-purple-700 transition-colors p-2 hover:bg-purple-50 rounded-full"
              title="Add Member"
            >
              <UserPlus size={18} />
            </button>
          </div>

          {/* Add Member Form */}
          {showAddMember && (
            <div className="mb-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <input
                type="text"
                value={newMemberName}
                onChange={(e) => setNewMemberName(e.target.value)}
                placeholder="Enter member name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') handleAddUser();
                }}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleAddUser}
                  disabled={!newMemberName.trim()}
                  className="flex-1 px-3 py-1.5 bg-gradient-to-r from-purple-500 to-teal-500 text-white rounded text-sm font-medium disabled:opacity-50"
                >
                  Add
                </button>
                <button
                  onClick={() => {
                    setShowAddMember(false);
                    setNewMemberName('');
                  }}
                  className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded text-sm font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Members List */}
          <div className="space-y-2">
            {group.members && group.members.length > 0 ? (
              group.members.map((member, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-400 flex items-center justify-center text-white font-semibold">
                    {member[0].toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{member}</div>
                    <div className="text-xs text-gray-600">Member</div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 text-center py-4">No members yet</p>
            )}
          </div>
        </div>

        {/* AI Agents Section */}
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex items-center gap-2 text-gray-700 font-medium mb-4">
            <div className="text-2xl">🤖</div>
            <span>AI Agents</span>
          </div>

          {/* Current Agents */}
          {groupAgents.length > 0 && (
            <div className="space-y-2 mb-4">
              {groupAgents.map((agent) => (
                <div key={agent.id} className="flex items-center gap-3 p-3 bg-gradient-to-r from-purple-50 to-teal-50 rounded-lg border border-purple-200">
                  <div className="text-2xl">{agent.avatar}</div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="text-xs text-purple-600">Active in group</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Available Agents to Add */}
          <div className="text-xs font-medium text-gray-600 mb-2 uppercase tracking-wide">Add Agent</div>
          <div className="space-y-2">
            {availableAgents
              .filter(agent => !group.agents?.includes(agent.id))
              .map((agent) => (
                <div
                  key={agent.id}
                  onClick={() => handleAddAgent(agent.id)}
                  className="flex items-center gap-3 p-3 hover:bg-gradient-to-r hover:from-purple-50 hover:to-teal-50 rounded-lg cursor-pointer transition-all border border-gray-200 hover:border-purple-300"
                  data-testid={`add-agent-${agent.id}`}
                >
                  <div className="text-2xl">{agent.avatar}</div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="text-xs text-gray-600">Click to add</div>
                  </div>
                  <div className="text-purple-500">
                    <UserPlus size={18} />
                  </div>
                </div>
              ))}
          </div>

          {availableAgents.filter(agent => !group.agents?.includes(agent.id)).length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">All agents added</p>
          )}
        </div>
      </div>
    </div>
  );
}