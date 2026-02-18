import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import Login from "./pages/Login";
import { fetchGroups } from "./api/chatApi.js";

export default function App() {
  const [user, setUser] = useState(null);
  const [groups, setGroups] = useState([]);
  const [activeGroup, setActiveGroup] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  async function loadGroups() {
    const token = localStorage.getItem("token");
    if (!token) {
      logout();
      return;
    }
    const data = await fetchGroups(token);
    const groupList = data?.groups || [];
    setGroups(groupList);
    if (!activeGroup && groupList.length > 0) {
      setActiveGroup(groupList[0]);
    }
  }

  useEffect(() => {
    if (user) {
      loadGroups();
    }
  }, [user]);

  function logout() {
    localStorage.clear();
    window.location.reload();
  }

  if (!user) {
    return <Login setUser={setUser} />;
  }

  return (
    <div data-testid="app-container" className="h-screen w-screen flex" style={{ background: "#0b141a" }}>
      <Sidebar
        groups={groups}
        activeGroup={activeGroup}
        setActiveGroup={setActiveGroup}
        reloadGroups={loadGroups}
        user={user}
        logout={logout}
      />

      {activeGroup && user ? (
        <ChatWindow group={activeGroup} user={user} />
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center" style={{ background: "#0b141a" }}>
          <div className="text-center">
            <div className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ background: "#202c33" }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#8696a0" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <h3 className="text-xl font-semibold" style={{ color: "#e9edef" }}>AgentChat</h3>
            <p className="text-sm mt-2" style={{ color: "#8696a0" }}>Select a group to start chatting</p>
          </div>
        </div>
      )}
    </div>
  );
}
