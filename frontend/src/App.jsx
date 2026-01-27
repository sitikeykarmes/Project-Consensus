import { useState, useEffect } from 'react';
import WhatsAppLayout from './components/WhatsAppLayout';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function App() {
  const [groups, setGroups] = useState([]);
  const [currentUser] = useState('User');
  const [availableAgents, setAvailableAgents] = useState([]);

  useEffect(() => {
    loadGroups();
    loadAgents();
  }, []);

  const loadGroups = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/groups`);
      setGroups(response.data.groups);
    } catch (error) {
      console.error('Error loading groups:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/agents`);
      setAvailableAgents(response.data.agents);
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  const handleCreateGroup = async (groupData) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/groups`, groupData);
      if (response.data.success) {
        loadGroups();
        return response.data.group;
      }
    } catch (error) {
      console.error('Error creating group:', error);
    }
  };

  const handleAddMember = async (groupId, memberId, memberType) => {
    try {
      await axios.post(`${BACKEND_URL}/api/groups/${groupId}/members`, {
        member_id: memberId,
        member_type: memberType
      });
      loadGroups();
    } catch (error) {
      console.error('Error adding member:', error);
    }
  };

  return (
    <WhatsAppLayout 
      groups={groups}
      currentUser={currentUser}
      availableAgents={availableAgents}
      onCreateGroup={handleCreateGroup}
      onAddMember={handleAddMember}
      onRefreshGroups={loadGroups}
    />
  );
}