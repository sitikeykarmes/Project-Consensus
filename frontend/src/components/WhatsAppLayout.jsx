import { useState } from 'react';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';
import CreateGroupModal from './CreateGroupModal';
import GroupInfoPanel from './GroupInfoPanel';
import { MessageSquare } from 'lucide-react';

export default function WhatsAppLayout({ 
  groups, 
  currentUser, 
  availableAgents,
  onCreateGroup,
  onAddMember,
  onRefreshGroups
}) {
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [showGroupInfo, setShowGroupInfo] = useState(false);

  const handleGroupSelect = (group) => {
    setSelectedGroup(group);
    setShowGroupInfo(false);
  };

  const handleCreateGroup = async (groupData) => {
    const newGroup = await onCreateGroup(groupData);
    if (newGroup) {
      setShowCreateGroup(false);
      setSelectedGroup(newGroup);
    }
  };

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-gray-100 via-gray-200 to-gray-300 flex items-center justify-center p-4" data-testid="whatsapp-layout">
      <div className="w-full h-full max-w-[1600px] mx-auto shadow-2xl flex bg-white rounded-2xl overflow-hidden border border-gray-300">
        {/* Sidebar */}
        <Sidebar 
          groups={groups}
          selectedGroup={selectedGroup}
          onGroupSelect={handleGroupSelect}
          onCreateGroup={() => setShowCreateGroup(true)}
          currentUser={currentUser}
        />

        {/* Chat Window */}
        {selectedGroup ? (
          <div className="flex-1 flex flex-col relative">
            <ChatWindow 
              group={selectedGroup}
              currentUser={currentUser}
              onShowGroupInfo={() => setShowGroupInfo(!showGroupInfo)}
              availableAgents={availableAgents}
            />
            
            {/* Group Info Panel */}
            {showGroupInfo && (
              <GroupInfoPanel 
                group={selectedGroup}
                onClose={() => setShowGroupInfo(false)}
                availableAgents={availableAgents}
                onAddMember={onAddMember}
                onRefresh={onRefreshGroups}
              />
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-br from-gray-50 via-purple-50 to-indigo-50 border-l border-gray-200">
            <div className="text-center max-w-md px-8">
              <div className="relative inline-block mb-8">
                <div className="w-56 h-56 bg-gradient-to-br from-purple-200 via-pink-200 to-red-200 rounded-full flex items-center justify-center shadow-2xl">
                  <MessageSquare className="w-28 h-28 text-purple-500" strokeWidth={1.5} />
                </div>
                <div className="absolute -top-4 -right-4 w-20 h-20 bg-gradient-to-br from-violet-400 to-fuchsia-500 rounded-full flex items-center justify-center shadow-xl animate-bounce">
                  <span className="text-4xl">🤖</span>
                </div>
              </div>
              <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-red-600 bg-clip-text text-transparent mb-4">
                AI-Powered Chat
              </h2>
              <p className="text-gray-700 text-lg leading-relaxed mb-6 font-medium">
                Select a group to start chatting or create a new group to collaborate with AI agents
              </p>
              <div className="flex flex-col gap-3 text-sm text-gray-600">
                <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-xl shadow-md">
                  <span className="text-2xl">✨</span>
                  <span className="font-medium">Create groups with multiple AI agents</span>
                </div>
                <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-xl shadow-md">
                  <span className="text-2xl">💬</span>
                  <span className="font-medium">Get instant responses and consensus</span>
                </div>
                <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-xl shadow-md">
                  <span className="text-2xl">🚀</span>
                  <span className="font-medium">Real-time collaboration and insights</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Create Group Modal */}
        {showCreateGroup && (
          <CreateGroupModal 
            onClose={() => setShowCreateGroup(false)}
            onCreate={handleCreateGroup}
            availableAgents={availableAgents}
          />
        )}
      </div>
    </div>
  );
}