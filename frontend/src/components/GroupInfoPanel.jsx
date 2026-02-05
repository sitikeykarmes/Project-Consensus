import { X, UserPlus, Users, Crown, Sparkles } from 'lucide-react';
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
    <div className="absolute right-0 top-0 bottom-0 w-96 bg-white shadow-2xl z-10 flex flex-col border-l-2 border-purple-200 animate-slideIn" data-testid="group-info-panel">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500 via-purple-600 to-indigo-600 px-6 py-4 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-2">
          <Sparkles className="text-white" size={20} />
          <h2 className="text-lg font-bold text-white">Group Info</h2>
        </div>
        <button 
          onClick={onClose}
          className="text-white hover:bg-white/20 p-2 rounded-full transition-all duration-200"
        >
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Group Avatar & Name */}
        <div className="px-6 py-8 text-center bg-gradient-to-b from-purple-50 via-white to-white border-b border-gray-200">
          <div className="relative inline-block">
            <div className="w-28 h-28 mx-auto rounded-full bg-gradient-to-br from-purple-400 via-pink-400 to-red-400 flex items-center justify-center text-white text-6xl mb-4 shadow-xl ring-4 ring-white">
              {group.avatar || '💬'}
            </div>
            {groupAgents.length > 0 && (
              <div className="absolute bottom-3 right-0 w-10 h-10 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg border-2 border-white">
                {groupAgents.length}
              </div>
            )}
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-1">{group.name}</h3>
          <div className="flex items-center justify-center gap-2 text-sm text-gray-600 font-medium">
            <Users size={16} />
            <span>Group • {group.members?.length || 0} member{(group.members?.length || 0) !== 1 ? 's' : ''}</span>
          </div>
          {groupAgents.length > 0 && (
            <div className="mt-2 inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-purple-100 to-fuchsia-100 text-purple-700 border border-purple-200">
              🤖 {groupAgents.length} AI Agent{groupAgents.length > 1 ? 's' : ''} Active
            </div>
          )}
        </div>

        {/* Members Section */}
        <div className="px-6 py-5 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-gray-800 font-bold">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center shadow-md">
                <Users size={16} className="text-white" />
              </div>
              <span>Members</span>
              <span className="text-xs font-normal text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
                {group.members?.length || 0}
              </span>
            </div>
            <button
              onClick={() => setShowAddMember(!showAddMember)}
              className="text-purple-600 hover:text-purple-700 transition-all duration-200 p-2 hover:bg-purple-50 rounded-full"
              title="Add Member"
            >
              <UserPlus size={18} />
            </button>
          </div>

          {/* Add Member Form */}
          {showAddMember && (
            <div className="mb-4 p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl border-2 border-purple-200 shadow-sm animate-fadeIn">
              <input
                type="text"
                value={newMemberName}
                onChange={(e) => setNewMemberName(e.target.value)}
                placeholder="Enter member name"
                className="w-full px-4 py-2.5 border-2 border-purple-300 rounded-lg mb-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') handleAddUser();
                }}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleAddUser}
                  disabled={!newMemberName.trim()}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg text-sm font-semibold disabled:opacity-50 hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  Add Member
                </button>
                <button
                  onClick={() => {
                    setShowAddMember(false);
                    setNewMemberName('');
                  }}
                  className="px-4 py-2 bg-white border-2 border-gray-300 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-50 transition-all duration-200"
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
                <div key={idx} className="flex items-center gap-3 p-3 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 rounded-xl transition-all duration-200 group">
                  <div className="w-11 h-11 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white font-bold shadow-md group-hover:shadow-lg transition-shadow duration-200">
                    {member[0].toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">{member}</div>
                    <div className="text-xs text-gray-600 font-medium">Member</div>
                  </div>
                  {idx === 0 && (
                    <Crown size={16} className="text-yellow-500" title="Admin" />
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-3">
                  <Users size={28} className="text-gray-400" />
                </div>
                <p className="text-sm text-gray-500 font-medium">No members yet</p>
              </div>
            )}
          </div>
        </div>

        {/* AI Agents Section */}
        <div className="px-6 py-5 bg-gradient-to-b from-white to-gray-50">
          <div className="flex items-center gap-2 text-gray-800 font-bold mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-full flex items-center justify-center shadow-md">
              <span className="text-lg">🤖</span>
            </div>
            <span>AI Agents</span>
            <span className="text-xs font-normal text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
              {groupAgents.length}
            </span>
          </div>

          {/* Current Agents */}
          {groupAgents.length > 0 && (
            <div className="space-y-2.5 mb-5">
              {groupAgents.map((agent) => (
                <div key={agent.id} className="flex items-center gap-3 p-4 bg-gradient-to-r from-purple-50 via-violet-50 to-fuchsia-50 rounded-xl border-2 border-purple-200 shadow-md hover:shadow-lg transition-all duration-200 group">
                  <div className="text-3xl group-hover:scale-110 transition-transform duration-200">{agent.avatar}</div>
                  <div className="flex-1">
                    <div className="font-bold text-gray-900">{agent.name}</div>
                    <div className="text-xs text-purple-600 font-semibold">✨ Active in group</div>
                  </div>
                  <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center shadow-md">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Available Agents to Add */}
          {availableAgents.filter(agent => !group.agents?.includes(agent.id)).length > 0 && (
            <>
              <div className="text-xs font-bold text-gray-700 mb-3 uppercase tracking-wider flex items-center gap-2">
                <Sparkles size={14} className="text-purple-500" />
                Add More Agents
              </div>
              <div className="space-y-2">
                {availableAgents
                  .filter(agent => !group.agents?.includes(agent.id))
                  .map((agent) => (
                    <div
                      key={agent.id}
                      onClick={() => handleAddAgent(agent.id)}
                      className="flex items-center gap-3 p-4 hover:bg-gradient-to-r hover:from-purple-50 hover:to-indigo-50 rounded-xl cursor-pointer transition-all duration-200 border-2 border-gray-200 hover:border-purple-300 hover:shadow-md group"
                      data-testid={`add-agent-${agent.id}`}
                    >
                      <div className="text-3xl group-hover:scale-110 transition-transform duration-200">{agent.avatar}</div>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{agent.name}</div>
                        <div className="text-xs text-gray-600 font-medium">Click to add to group</div>
                      </div>
                      <div className="text-purple-500 group-hover:text-purple-700 transition-colors duration-200">
                        <UserPlus size={20} />
                      </div>
                    </div>
                  ))}
              </div>
            </>
          )}

          {availableAgents.filter(agent => !group.agents?.includes(agent.id)).length === 0 && (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto bg-gradient-to-br from-purple-100 to-fuchsia-100 rounded-full flex items-center justify-center mb-3">
                <span className="text-3xl">🎉</span>
              </div>
              <p className="text-sm text-purple-600 font-semibold">All agents added!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}