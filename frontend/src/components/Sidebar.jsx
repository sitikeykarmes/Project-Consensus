import { useState } from "react";
import { LogOut, Plus, MessageSquare, Search } from "lucide-react";
import CreateGroupModal from "./CreateGroupModal";

export default function Sidebar({
  groups,
  activeGroup,
  setActiveGroup,
  reloadGroups,
  user,
  logout,
}) {
  const [showModal, setShowModal] = useState(false);
  const [search, setSearch] = useState("");

  const filtered =
    groups?.filter((g) =>
      g.name.toLowerCase().includes(search.toLowerCase()),
    ) || [];

  function getInitials(name) {
    return (
      name
        ?.split(" ")
        .map((w) => w[0])
        .join("")
        .slice(0, 2)
        .toUpperCase() || "GC"
    );
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
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
            style={{ background: "#00a884", color: "#fff" }}
          >
            {user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <span
            className="text-sm font-medium truncate max-w-[140px]"
            style={{ color: "#e9edef" }}
          >
            {user?.email}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            data-testid="create-group-button"
            onClick={() => setShowModal(true)}
            className="p-4 rounded-lg transition-colors"
            style={{ color: "#8696a0" }}
            title="New Group"
          >
            <Plus size={20} />
          </button>
          <button
            data-testid="logout-button"
            onClick={logout}
            className="p-4 rounded-lg transition-colors"
            style={{ color: "#8696a0" }}
            title="Logout"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="px-4 py-3" style={{ background: "#111b21" }}>
        <div className="relative flex items-center">
          {/* Icon */}
          <Search
            size={18}
            className="absolute left-4"
            style={{ color: "#8696a0" }}
          />

          {/* Input */}
          <input
            type="text"
            placeholder="Search groups..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-10 rounded-xl text-sm focus:outline-none"
            style={{
              background: "#202c33",
              color: "#e9edef",

              /* 🔥 Force padding so text starts AFTER icon */
              paddingLeft: "48px",
              paddingRight: "14px",
            }}
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
                className="flex items-center gap-3 px-4 py-3 cursor-pointer transition-all rounded-xl mx-2 my-1"
                style={{
                  background: isActive ? "#2a3942" : "#111b21",

                  /* Space + card feel */
                  border: isActive
                    ? "1px solid #00a884"
                    : "1px solid transparent",

                  /* Smooth hover look */
                  boxShadow: isActive ? "0 0 6px rgba(0,168,132,0.3)" : "none",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.background = "#202c33")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.background = isActive
                    ? "#2a3942"
                    : "#111b21")
                }
              >
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                  style={{ background: "#6a7175", color: "#fff" }}
                >
                  {getInitials(group.name)}
                </div>
                <div className="flex-1 min-w-0">
                  <p
                    className="text-sm font-semibold truncate"
                    style={{ color: "#e9edef" }}
                  >
                    {group.name}
                  </p>
                  <p
                    className="text-xs truncate mt-0.5"
                    style={{ color: "#8696a0" }}
                  >
                    {group.agents?.length || 0} agents
                  </p>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center mt-8 px-4">
            <MessageSquare
              size={32}
              className="mx-auto mb-2"
              style={{ color: "#2a3942" }}
            />
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
        <CreateGroupModal
          close={() => setShowModal(false)}
          reloadGroups={reloadGroups}
        />
      )}
    </div>
  );
}
