import { useEffect, useState } from "react";

import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";

import Login from "./pages/Login";
import { fetchGroups } from "./api/ChatApi";

export default function App() {
  const [user, setUser] = useState(null);

  const [groups, setGroups] = useState([]);
  const [activeGroup, setActiveGroup] = useState(null);

  // ---------------------------------------------------
  // ✅ Load logged-in user from localStorage
  // ---------------------------------------------------
  useEffect(() => {
    const savedUser = localStorage.getItem("user");

    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  // ---------------------------------------------------
  // ✅ Load groups ONLY after login
  // ---------------------------------------------------
  async function loadGroups() {
    const token = localStorage.getItem("token");

    if (!token) {
      console.log("No token found, logout...");
      logout();
      return;
    }

    const data = await fetchGroups(token);

    // ✅ Ensure safe array
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

  // ---------------------------------------------------
  // ✅ Logout Function
  // ---------------------------------------------------
  function logout() {
    localStorage.clear();
    window.location.reload();
  }

  // ---------------------------------------------------
  // ✅ If not logged in → Show Login Page
  // ---------------------------------------------------
  if (!user) {
    return <Login setUser={setUser} />;
  }

  // ---------------------------------------------------
  // ✅ If logged in → Show Chat App
  // ---------------------------------------------------
  return (
    <div className="h-screen w-screen flex bg-[#f0f2f5]">
      {/* Sidebar */}
      <Sidebar
        groups={groups}
        activeGroup={activeGroup}
        setActiveGroup={setActiveGroup}
        reloadGroups={loadGroups}
        user={user}
        logout={logout}
      />

      {/* Chat Window */}
      {activeGroup && user && <ChatWindow group={activeGroup} user={user} />}
    </div>
  );
}
