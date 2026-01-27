import { useState } from 'react';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';
import CreateGroupModal from './CreateGroupModal';
import GroupInfoPanel from './GroupInfoPanel';

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
    <div className="h-screen w-screen bg-[#F0F2F5] flex items-center justify-center" data-testid="whatsapp-layout">
      <div className="w-full h-full max-w-[1600px] mx-auto shadow-2xl flex bg-white">
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
          <div className="flex-1 flex flex-col items-center justify-center bg-[#F0F2F5] border-l border-gray-200">
            <div className="text-center">
              <div className="w-48 h-48 mx-auto mb-8 bg-gradient-to-br from-purple-100 to-teal-100 rounded-full flex items-center justify-center">
                <svg className="w-24 h-24 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h2 className="text-3xl font-light text-gray-600 mb-3">WhatsApp Chat</h2>
              <p className="text-gray-500 text-sm max-w-md">
                Select a group to start chatting or create a new group to begin
              </p>
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