import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import { fetchGroups } from "./api/ChatApi";

export default function App() {
  const [groups, setGroups] = useState([]);
  const [activeGroup, setActiveGroup] = useState(null);

  // Load groups from backend
  async function loadGroups() {
    const data = await fetchGroups();
    setGroups(data.groups);
    if (!activeGroup && data.groups.length > 0) {
      setActiveGroup(data.groups[0]);
    }
  }

  useEffect(() => {
    loadGroups();
  }, []);

  return (
    <div className="h-screen w-screen flex bg-[#f0f2f5]">
      {/* Sidebar */}
      <Sidebar
        groups={groups}
        activeGroup={activeGroup}
        setActiveGroup={setActiveGroup}
        reloadGroups={loadGroups}
      />

      {/* Chat Window */}
      {activeGroup && <ChatWindow group={activeGroup} />}
    </div>
  );
}
