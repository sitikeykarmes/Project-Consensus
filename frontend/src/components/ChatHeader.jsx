import { useState, useEffect } from "react";
import { Users, UserPlus, Bot, Wifi, WifiOff } from "lucide-react";
import AddMembersModal from "./AddMembersModal";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "";

export default function ChatHeader({ group, connected }) {
  const [showAddMembers, setShowAddMembers] = useState(false);
  const [members, setMembers] = useState([]);

  async function loadMembers() {
    const token = localStorage.getItem("token");
    if (!token || !group?.id) return;
    try {
      const res = await fetch(`${BASE_URL}/groups/${group.id}/members`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMembers(data.members || []);
      }
    } catch (err) {
      console.error("Failed to load members:", err);
    }
  }

  useEffect(() => {
    loadMembers();
  }, [group?.id]);

  function getInitials(name) {
    return name?.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "GC";
  }

  return (
    <>
      <div
        data-testid="chat-header"
        className="h-14 px-4 flex items-center justify-between shrink-0 relative z-10"
        style={{ background: "#202c33", borderBottom: "1px solid #2a3942" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold"
            style={{ background: "#6a7175", color: "#fff" }}
          >
            {getInitials(group.name)}
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: "#e9edef" }}>
              {group.name}
            </p>
            <div className="flex items-center gap-3 text-[11px]" style={{ color: "#8696a0" }}>
              <span className="flex items-center gap-1">
                <Bot size={11} /> {group.agents?.length || 0} agents
              </span>
              <span className="flex items-center gap-1">
                <Users size={11} /> {members.length} members
              </span>
              <span className="flex items-center gap-1">
                {connected ? (
                  <>
                    <Wifi size={11} style={{ color: "#00a884" }} />
                    <span style={{ color: "#00a884" }}>Online</span>
                  </>
                ) : (
                  <>
                    <WifiOff size={11} style={{ color: "#ef4444" }} />
                    <span style={{ color: "#ef4444" }}>Connecting</span>
                  </>
                )}
              </span>
            </div>
          </div>
        </div>

        <button
          data-testid="add-members-button"
          onClick={() => setShowAddMembers(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
          style={{ background: "#2a3942", color: "#8696a0", border: "1px solid #2a3942" }}
        >
          <UserPlus size={14} />
          Add Members
        </button>
      </div>

      {showAddMembers && (
        <AddMembersModal
          groupId={group.id}
          close={() => setShowAddMembers(false)}
          onMembersAdded={loadMembers}
        />
      )}
    </>
  );
}
