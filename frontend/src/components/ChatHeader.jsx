import { useState, useEffect } from "react";
import {
  Users,
  UserPlus,
  Bot,
  Wifi,
  WifiOff,
  ChevronDown,
  Trash2,
  X,
  AlertTriangle,
} from "lucide-react";
import AddMembersModal from "./AddMembersModal";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "";

const AGENT_STYLES = {
  agent_research: {
    color: "#3b82f6",
    label: "Agent 1",
    role: "openai/gpt-oss-10b",
  },
  agent_analysis: {
    color: "#f59e0b",
    label: "Agent 2",
    role: "meta-llama/llama-4-scout-17b-16e-instruct",
  },
  agent_synthesis: {
    color: "#8b5cf6",
    label: "Agent 3",
    role: "moonshotai/kimi-k2-instruct",
  },
};

function DeleteGroupModal({ group, onConfirm, onClose, loading }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.7)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm rounded-2xl p-6 mx-4"
        style={{ background: "#1f2c34", border: "1px solid #2a3942" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-center mb-4">
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center"
            style={{ background: "rgba(239,68,68,0.15)" }}
          >
            <AlertTriangle size={28} style={{ color: "#ef4444" }} />
          </div>
        </div>
        <h2
          className="text-center text-base font-semibold mb-1"
          style={{ color: "#e9edef" }}
        >
          Delete "{group.name}"?
        </h2>
        <p
          className="text-center text-xs mb-6 leading-relaxed"
          style={{ color: "#8696a0" }}
        >
          This will permanently delete the group, all messages, and conversation
          history. This action cannot be undone.
        </p>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium"
            style={{ background: "#2a3942", color: "#8696a0" }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50"
            style={{ background: "#ef4444", color: "#fff" }}
          >
            {loading ? "Deleting…" : "Delete Group"}
          </button>
        </div>
      </div>
    </div>
  );
}

function GroupInfoPanel({ group, members, onClose, onDeleteClick }) {
  const agents = group.agents || [];

  return (
    <div
      className="fixed inset-0 z-40 flex justify-end"
      style={{ background: "rgba(0,0,0,0.4)" }}
      onClick={onClose}
    >
      <div
        className="h-full w-80 flex flex-col overflow-hidden"
        style={{
          background: "#0b141a",
          borderLeft: "1px solid #2a3942",
          animation: "slideInRight 0.2s ease-out",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4 shrink-0"
          style={{ background: "#202c33", borderBottom: "1px solid #2a3942" }}
        >
          <span className="text-sm font-semibold" style={{ color: "#e9edef" }}>
            Group Info
          </span>
          <button onClick={onClose} style={{ color: "#8696a0" }}>
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {/* Group Identity */}
          <div
            className="flex flex-col items-center py-8 px-5"
            style={{ borderBottom: "1px solid #2a3942" }}
          >
            <div
              className="w-20 h-20 rounded-full flex items-center justify-center text-2xl font-bold mb-3"
              style={{ background: "#2a3942", color: "#e9edef" }}
            >
              {group.name?.slice(0, 2).toUpperCase() || "GC"}
            </div>
            <p className="text-base font-semibold" style={{ color: "#e9edef" }}>
              {group.name}
            </p>
            <p className="text-xs mt-1" style={{ color: "#8696a0" }}>
              {members.length} member{members.length !== 1 ? "s" : ""} ·{" "}
              {agents.length} agent{agents.length !== 1 ? "s" : ""}
            </p>
          </div>

          {/* Agents */}
          <div
            className="px-5 py-4"
            style={{ borderBottom: "1px solid #2a3942" }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Bot size={14} style={{ color: "#00a884" }} />
              <span
                className="text-xs font-semibold uppercase tracking-wider"
                style={{ color: "#00a884" }}
              >
                AI Agents
              </span>
            </div>
            <div className="space-y-2">
              {agents.length === 0 && (
                <p className="text-xs" style={{ color: "#8696a0" }}>
                  No agents in this group
                </p>
              )}
              {agents.map((agentId, idx) => {
                const style = AGENT_STYLES[agentId] || {
                  color: "#8696a0",
                  label: `Agent ${idx + 1}`,
                  role: "Agent",
                };
                return (
                  <div
                    key={agentId}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl"
                    style={{ background: "#1f2c34" }}
                  >
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                      style={{
                        background: `${style.color}22`,
                        color: style.color,
                      }}
                    >
                      {style.label.split(" ")[1]}
                    </div>
                    <div>
                      <p
                        className="text-xs font-semibold"
                        style={{ color: "#e9edef" }}
                      >
                        {style.label}
                      </p>
                      <p className="text-[10px]" style={{ color: "#8696a0" }}>
                        {style.role}
                      </p>
                    </div>
                    <div
                      className="w-2 h-2 rounded-full ml-auto"
                      style={{ background: "#00a884" }}
                    />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Members */}
          <div
            className="px-5 py-4"
            style={{ borderBottom: "1px solid #2a3942" }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Users size={14} style={{ color: "#8696a0" }} />
              <span
                className="text-xs font-semibold uppercase tracking-wider"
                style={{ color: "#8696a0" }}
              >
                Members ({members.length})
              </span>
            </div>
            <div className="space-y-1">
              {members.length === 0 && (
                <p className="text-xs" style={{ color: "#8696a0" }}>
                  No members yet
                </p>
              )}
              {members.map((member, idx) => (
                <div
                  key={member.id || idx}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl"
                  style={{ background: "#1f2c34" }}
                >
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                    style={{ background: "#2a3942", color: "#8696a0" }}
                  >
                    {member.email?.[0]?.toUpperCase() || "U"}
                  </div>
                  <p
                    className="text-xs font-medium truncate"
                    style={{ color: "#e9edef" }}
                  >
                    {member.email}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Delete button */}
        <div
          className="px-5 py-4 shrink-0"
          style={{ borderTop: "1px solid #2a3942" }}
        >
          <button
            onClick={onDeleteClick}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium"
            style={{
              background: "rgba(239,68,68,0.1)",
              color: "#ef4444",
              border: "1px solid rgba(239,68,68,0.2)",
            }}
          >
            <Trash2 size={15} />
            Delete Group
          </button>
        </div>
      </div>

      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>
    </div>
  );
}

export default function ChatHeader({ group, connected, onGroupDeleted }) {
  const [showAddMembers, setShowAddMembers] = useState(false);
  const [showInfoPanel, setShowInfoPanel] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [members, setMembers] = useState([]);

  async function loadMembers() {
    const token = localStorage.getItem("token");
    if (!token || !group?.id) return;
    try {
      const res = await fetch(`${BASE_URL}/api/groups/${group.id}/members`, {
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

  async function handleDeleteGroup() {
    const token = localStorage.getItem("token");
    if (!token) return;
    setDeleteLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/api/groups/${group.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setShowDeleteModal(false);
        setShowInfoPanel(false);
        onGroupDeleted?.();
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Failed to delete group.");
      }
    } catch {
      alert("Network error while deleting group.");
    } finally {
      setDeleteLoading(false);
    }
  }

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
    <>
      <div
        data-testid="chat-header"
        className="h-14 px-4 flex items-center justify-between shrink-0 relative z-10"
        style={{ background: "#202c33", borderBottom: "1px solid #2a3942" }}
      >
        <button
          className="flex items-center gap-3 rounded-lg px-1 py-1"
          onClick={() => setShowInfoPanel(true)}
          title="View group info"
        >
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
            style={{ background: "#6a7175", color: "#fff" }}
          >
            {getInitials(group.name)}
          </div>
          <div className="text-left">
            <div className="flex items-center gap-1">
              <p className="text-sm font-semibold" style={{ color: "#e9edef" }}>
                {group.name}
              </p>
              <ChevronDown size={13} style={{ color: "#8696a0" }} />
            </div>
            <div
              className="flex items-center gap-3 text-[11px]"
              style={{ color: "#8696a0" }}
            >
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
        </button>

        <button
          data-testid="add-members-button"
          onClick={() => setShowAddMembers(true)}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium"
          style={{
            background: "#2a3942",
            color: "#8696a0",
            border: "1px solid #2a3942",
          }}
        >
          <UserPlus size={15} />
          Add Members
        </button>
      </div>

      {showInfoPanel && (
        <GroupInfoPanel
          group={group}
          members={members}
          onClose={() => setShowInfoPanel(false)}
          onDeleteClick={() => {
            setShowInfoPanel(false);
            setShowDeleteModal(true);
          }}
        />
      )}

      {showDeleteModal && (
        <DeleteGroupModal
          group={group}
          loading={deleteLoading}
          onConfirm={handleDeleteGroup}
          onClose={() => setShowDeleteModal(false)}
        />
      )}

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
