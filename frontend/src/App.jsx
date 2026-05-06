import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import Login from "./pages/Login";
import LandingPage from "./pages/LandingPage";
import { fetchGroups } from "./api/chatApi.js";

export default function App() {
  const [user, setUser] = useState(null);
  const [groups, setGroups] = useState([]);
  const [activeGroup, setActiveGroup] = useState(null);
  const [showLogin, setShowLogin] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  async function loadGroups(silent = false) {
    const token = localStorage.getItem("token");
    if (!token) {
      logout();
      return;
    }
    try {
      const data = await fetchGroups(token);
      const groupList = data?.groups || [];
      setGroups(groupList);
      if (!activeGroup && groupList.length > 0 && !silent) {
        setActiveGroup(groupList[0]);
      }
    } catch (error) {
      if (error.message === "UNAUTHORIZED") {
        logout();
      } else {
        console.error("Failed to load groups:", error);
      }
    }
  }

  useEffect(() => {
    let interval;
    if (user) {
      loadGroups();
      interval = setInterval(() => {
        loadGroups(true);
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [user]);

  // Called by ChatWindow → ChatHeader after successful delete
  function handleGroupDeleted(deletedGroupId) {
    // Remove from sidebar list
    setGroups((prev) => prev.filter((g) => g.id !== deletedGroupId));
    // If deleted group was active, clear it → shows empty state
    setActiveGroup((prev) => (prev?.id === deletedGroupId ? null : prev));
  }

  function logout() {
    localStorage.clear();
    window.location.reload();
  }

  if (!user) {
    if (showLogin) return <Login setUser={setUser} />;
    return <LandingPage onLoginClick={() => setShowLogin(true)} />;
  }

  return (
    <div
      data-testid="app-container"
      className="h-screen w-screen flex"
      style={{ background: "var(--bg-app)", color: "var(--text-primary)" }}
    >
      <Sidebar
        groups={groups}
        activeGroup={activeGroup}
        setActiveGroup={setActiveGroup}
        reloadGroups={loadGroups}
        user={user}
        logout={logout}
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
      />

      {activeGroup && user ? (
        <ChatWindow
          group={activeGroup}
          user={user}
          onGroupDeleted={handleGroupDeleted}
          isSidebarOpen={isSidebarOpen}
          setIsSidebarOpen={setIsSidebarOpen}
        />
      ) : (
        <div
          className="flex-1 flex flex-col items-center justify-center relative"
          style={{ background: "var(--bg-app)" }}
        >
          <div className="text-center">
            <div
              className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center"
              style={{ background: "var(--bg-header)", border: "1px solid var(--border)" }}
            >
              <svg
                width="40"
                height="40"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#8696a0"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold tracking-wide" style={{ color: "var(--accent)" }}>
              Project Consensus
            </h3>
            <p className="text-sm mt-2" style={{ color: "var(--text-secondary)" }}>
              Select a group to start collaborating
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
