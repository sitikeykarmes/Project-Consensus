import { useState } from "react";
import { LogOut, Plus, MessageSquare, Search } from "lucide-react";
import CreateGroupModal from "./CreateGroupModal";

export default function Sidebar({ groups, activeGroup, setActiveGroup, reloadGroups, user, logout }) {
  const [showModal, setShowModal] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = groups?.filter((g) =>
    g.name.toLowerCase().includes(search.toLowerCase())
  ) || [];

  function getInitials(name) {
    return name?.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "GC";
  }

  return (
    <div
      data-testid="sidebar"
      className="flex flex-col"
      style={{
        width: "30%",
        minWidth: "320px",
        background: "#111b21",
        borderRight: "1px solid #2a3942",
      }}
    >
      {/* Header */}
      <div
        className="h-14 px-4 flex items-center justify-between shrink-0"
        style={{ background: "#202c33" }}
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold" style={{ background: "#00a884", color: "#fff" }}>
            {user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <span className="text-sm font-medium truncate max-w-[140px]" style={{ color: "#e9edef" }}>
            {user?.email}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            data-testid="create-group-button"
            onClick={() => setShowModal(true)}
            className="p-2 rounded-lg transition-colors"
            style={{ color: "#8696a0" }}
            title="New Group"
          >
            <Plus size={20} />
          </button>
          <button
            data-testid="logout-button"
            onClick={logout}
            className="p-2 rounded-lg transition-colors"
            style={{ color: "#8696a0" }}
            title="Logout"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="px-3 py-2" style={{ background: "#111b21" }}>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "#8696a0" }} />
          <input
            data-testid="group-search-input"
            type="text"
            placeholder="Search groups..."
            className="w-full pl-9 pr-4 py-2 rounded-lg text-sm focus:outline-none"
            style={{ background: "#202c33", color: "#e9edef", border: "none" }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Group List */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length > 0 ? (
          filtered.map((group) => {
            const isActive = activeGroup?.id === group.id;
            return (
              <div
                key={group.id}
                data-testid={`group-item-${group.id}`}
                onClick={() => setActiveGroup(group)}
                className="flex items-center gap-3 px-4 py-3 cursor-pointer transition-all"
                style={{
                  background: isActive ? "#2a3942" : "transparent",
                  borderLeft: isActive ? "3px solid #00a884" : "3px solid transparent",
                  borderBottom: "1px solid rgba(42,57,66,0.5)",
                }}
              >
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                  style={{ background: "#6a7175", color: "#fff" }}
                >
                  {getInitials(group.name)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold truncate" style={{ color: "#e9edef" }}>
                    {group.name}
                  </p>
                  <p className="text-xs truncate mt-0.5" style={{ color: "#8696a0" }}>
                    {group.agents?.length || 0} agents
                  </p>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center mt-8 px-4">
            <MessageSquare size={32} className="mx-auto mb-2" style={{ color: "#2a3942" }} />
            <p className="text-sm" style={{ color: "#8696a0" }}>
              {search ? "No groups found" : "No groups yet"}
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="mt-3 text-sm font-medium"
              style={{ color: "#00a884" }}
            >
              Create your first group
            </button>
          </div>
        )}
      </div>

      {showModal && (
        <CreateGroupModal close={() => setShowModal(false)} reloadGroups={reloadGroups} />
      )}
    </div>
  );
}
