import { useState } from "react";
import { LogOut, Plus, MessageSquare, Search } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import CreateGroupModal from "./CreateGroupModal";

export default function Sidebar({
  groups,
  activeGroup,
  setActiveGroup,
  reloadGroups,
  user,
  logout,
  isSidebarOpen,
  setIsSidebarOpen,
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
      className="flex flex-col h-full transition-all duration-300 ease-in-out"
      style={{
        width: isSidebarOpen ? "320px" : "72px",
        minWidth: isSidebarOpen ? "320px" : "72px",
        background: "var(--bg-sidebar)",
        borderRight: "1px solid var(--border)",
        overflowX: "hidden",
      }}
    >
      {/* Top Section: Toggle, New Group & Search */}
      <div className="p-4 shrink-0 flex flex-col gap-4">
        <div className="flex items-center">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 rounded-lg hover:bg-[var(--border)] transition-colors"
          >
            {isSidebarOpen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="9" y1="3" x2="9" y2="21"></line>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            )}
          </button>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className={`flex items-center rounded-full transition-colors hover:opacity-90 overflow-hidden ${isSidebarOpen ? 'justify-start' : 'justify-center'}`}
          style={{ background: "var(--bg-header)", border: "1px solid var(--border)", padding: "10px" }}
          title={!isSidebarOpen ? "New Collaboration" : ""}
        >
          <div className={`flex items-center justify-center shrink-0 ${isSidebarOpen ? 'ml-1' : ''}`}>
            <Plus size={18} style={{ color: "var(--accent)" }} />
          </div>
          <span 
            className={`font-semibold text-sm whitespace-nowrap overflow-hidden transition-all duration-300 ease-in-out ${isSidebarOpen ? 'max-w-[200px] opacity-100 ml-3' : 'max-w-0 opacity-0 ml-0'}`} 
            style={{ color: "var(--text-primary)" }}
          >
            New Collaboration
          </span>
        </button>

        <div className={`overflow-hidden transition-all duration-300 ease-in-out ${isSidebarOpen ? 'max-h-12 opacity-100' : 'max-h-0 opacity-0'}`}>
          <div className="relative flex items-center">
            <Search size={16} className="absolute left-4" style={{ color: "var(--text-secondary)" }} />
            <input
              type="text"
              placeholder="Search recent chats..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-10 rounded-full text-sm focus:outline-none"
              style={{
                background: "var(--bg-header)",
                color: "var(--text-primary)",
                paddingLeft: "42px",
                paddingRight: "14px",
                border: "1px solid var(--border)"
              }}
            />
          </div>
        </div>
      </div>

      <div className={`px-4 shrink-0 overflow-hidden transition-all duration-300 ease-in-out ${isSidebarOpen ? 'max-h-8 opacity-100 pb-2' : 'max-h-0 opacity-0 pb-0'}`}>
        <span className="text-xs font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: "var(--text-secondary)" }}>
          Recent
        </span>
      </div>

      {/* Middle Section: Group List */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden scrollbar-hide">
        {isSidebarOpen && (
          filtered.length > 0 ? (
            <AnimatePresence initial={false}>
              {filtered.map((group) => {
                const isActive = activeGroup?.id === group.id;
                return (
                  <motion.div
                    layout="position"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ type: "spring", stiffness: 350, damping: 25 }}
                    key={group.id}
                    onClick={() => setActiveGroup(group)}
                    className="flex items-center cursor-pointer transition-all rounded-xl mx-2 my-1 overflow-hidden"
                    style={{
                      padding: "8px",
                      background: isActive ? "var(--bg-header)" : "transparent",
                      border: isActive ? "1px solid var(--border-highlight)" : "1px solid transparent",
                      boxShadow: isActive ? "0 0 8px rgba(212, 175, 55, 0.15)" : "none",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) e.currentTarget.style.background = "var(--bg-header)";
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) e.currentTarget.style.background = "transparent";
                    }}
                    title={!isSidebarOpen ? group.name : ""}
                  >
                    <div className="relative shrink-0 flex items-center justify-center w-10 h-10 ml-[2px]">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                        style={{ background: "var(--bg-app)", color: "var(--accent)", border: "1px solid var(--border-highlight)" }}
                      >
                        {getInitials(group.name)}
                      </div>
                      {group.unread_count > 0 && !isActive && !isSidebarOpen && (
                        <div 
                          className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full"
                          style={{ background: "var(--accent)", border: "2px solid var(--bg-sidebar)" }}
                        />
                      )}
                    </div>
                    
                    <div className={`flex-1 min-w-0 transition-all duration-300 ease-in-out ${isSidebarOpen ? 'max-w-[220px] opacity-100 ml-3' : 'max-w-0 opacity-0 ml-0'}`}>
                      <div className="flex justify-between items-baseline mb-0.5">
                        <p className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                          {group.name}
                        </p>
                      </div>
                      <div className="flex justify-between items-center mt-0.5">
                        <p className="text-xs truncate flex-1" style={{ color: "var(--text-secondary)", minWidth: 0 }}>
                          {group.last_message_content || `${group.agents?.length || 0} agents`}
                        </p>
                        {group.unread_count > 0 && !isActive && (
                          <div 
                            className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ml-2 shrink-0"
                            style={{ background: "var(--accent)", color: "var(--bg-app)" }}
                          >
                            {group.unread_count}
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          ) : (
            <div className={`text-center mt-8 px-4 overflow-hidden transition-all duration-300 ${isSidebarOpen ? 'max-h-[100px] opacity-100' : 'max-h-0 opacity-0'}`}>
              <MessageSquare size={32} className="mx-auto mb-2" style={{ color: "var(--border)" }} />
              <p className="text-sm whitespace-nowrap" style={{ color: "var(--text-secondary)" }}>
                {search ? "No matches" : "No collaborations"}
              </p>
            </div>
          )
        )}
      </div>

      {/* Bottom Section: Account Information */}
      <div className="p-3 shrink-0 mt-auto border-t overflow-hidden" style={{ borderColor: "var(--border)", background: "var(--bg-sidebar)" }}>
        <div className="flex items-center rounded-xl overflow-hidden transition-all duration-300" style={{ background: isSidebarOpen ? "var(--bg-header)" : "transparent", padding: isSidebarOpen ? "8px" : "4px" }}>
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ml-[2px]"
            style={{ background: "var(--bg-app)", color: "var(--accent)", border: "1px solid var(--border)" }}
            title={user?.email}
          >
            {user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          
          <div className={`flex items-center justify-between transition-all duration-300 ease-in-out ${isSidebarOpen ? 'max-w-[200px] opacity-100 ml-3 flex-1' : 'max-w-0 opacity-0 ml-0'}`}>
            <span className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
              {user?.email}
            </span>
            <button
              onClick={logout}
              className="p-2 rounded-lg transition-colors hover:bg-[var(--border)] shrink-0 ml-2"
              style={{ color: "var(--text-secondary)" }}
              title="Sign Out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
        
        {/* Render a standalone logout button when closed, positioned beautifully */}
        <div className={`flex justify-center transition-all duration-300 ease-in-out overflow-hidden ${!isSidebarOpen ? 'max-h-12 opacity-100 mt-2' : 'max-h-0 opacity-0 mt-0'}`}>
          <button
            onClick={logout}
            className="p-2 rounded-lg transition-colors hover:bg-[var(--bg-header)]"
            style={{ color: "var(--text-secondary)" }}
            title="Sign Out"
          >
            <LogOut size={18} />
          </button>
        </div>
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
