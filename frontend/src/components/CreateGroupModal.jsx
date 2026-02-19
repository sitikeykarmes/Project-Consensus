import { useEffect, useState } from "react";
import { fetchAgents } from "../api/chatApi";
import { X, Plus, Bot, Users, Mail } from "lucide-react";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "";

export default function CreateGroupModal({ close, reloadGroups }) {
  const [name, setName] = useState("");
  const [agents, setAgents] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [memberEmail, setMemberEmail] = useState("");
  const [memberEmails, setMemberEmails] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadAgents() {
      try {
        const data = await fetchAgents();
        setAgents(data.agents);
      } catch (err) {
        console.error("Failed to load agents");
      }
    }
    loadAgents();
  }, []);

  function toggleAgent(agentId) {
    if (selectedAgents.includes(agentId)) {
      setSelectedAgents(selectedAgents.filter((a) => a !== agentId));
    } else {
      setSelectedAgents([...selectedAgents, agentId]);
    }
  }

  function addMemberEmail() {
    const email = memberEmail.trim().toLowerCase();
    if (!email) return;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert("Please enter a valid email address");
      return;
    }
    if (memberEmails.includes(email)) {
      alert("Email already added");
      return;
    }
    setMemberEmails([...memberEmails, email]);
    setMemberEmail("");
  }

  function removeMemberEmail(email) {
    setMemberEmails(memberEmails.filter((e) => e !== email));
  }

  function handleEmailKeyPress(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      addMemberEmail();
    }
  }

  async function handleCreate() {
    if (!name.trim()) {
      alert("Group name cannot be empty");
      return;
    }
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Login required");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/api/groups/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: name,
          agents: selectedAgents,
          member_emails: memberEmails,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        alert("Failed: " + (data.detail || "Unknown error"));
        setLoading(false);
        return;
      }

      reloadGroups();
      close();
    } catch (err) {
      console.error(err);
      alert("Server error");
    }
    setLoading(false);
  }

  return (
    <div
      className="fixed inset-0 flex justify-center items-center z-50"
      style={{ background: "rgba(0,0,0,0.6)" }}
    >
      <div
        data-testid="create-group-modal"
        className="w-[480px] max-h-[85vh] overflow-y-auto rounded-xl shadow-2xl"
        style={{ background: "#202c33", border: "1px solid #2a3942" }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4"
          style={{ borderBottom: "1px solid #2a3942" }}
        >
          <h2 className="text-base font-semibold" style={{ color: "#e9edef" }}>
            Create New Group
          </h2>
          <button
            onClick={close}
            className="p-1 rounded-lg"
            style={{ color: "#8696a0" }}
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Group Name */}
          <div>
            <label
              className="text-xs font-medium mb-1.5 block"
              style={{ color: "#8696a0" }}
            >
              Group Name
            </label>
            <input
              data-testid="group-name-input"
              className="w-full px-4 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-1"
              placeholder="Enter group name..."
              style={{
                background: "#2a3942",
                color: "#e9edef",
                border: "none",
              }}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {/* Agent Selection */}
          <div>
            <label
              className="text-xs font-medium mb-2 flex items-center gap-1.5"
              style={{ color: "#8696a0" }}
            >
              <Bot size={14} /> Select AI Agents
            </label>
            <div className="space-y-2">
              {agents.map((agent) => (
                <label
                  key={agent.id}
                  data-testid={`agent-checkbox-${agent.id}`}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all"
                  style={{
                    background: selectedAgents.includes(agent.id)
                      ? "rgba(0,168,132,0.1)"
                      : "#2a3942",
                    border: `1px solid ${selectedAgents.includes(agent.id) ? "#00a884" : "transparent"}`,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedAgents.includes(agent.id)}
                    onChange={() => toggleAgent(agent.id)}
                    className="accent-[#00a884]"
                  />
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                    style={{ background: "#00a884", color: "#fff" }}
                  >
                    {agent.avatar || "AI"}
                  </div>
                  <span className="text-sm" style={{ color: "#e9edef" }}>
                    {agent.name}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Members */}
          <div>
            <label
              className="text-xs font-medium mb-2 flex items-center gap-1.5"
              style={{ color: "#8696a0" }}
            >
              <Users size={14} /> Invite Members (Optional)
            </label>
            <div className="flex gap-2">
              <input
                data-testid="member-email-input"
                type="email"
                className="flex-1 px-4 py-2.5 rounded-lg text-sm focus:outline-none"
                placeholder="Enter email..."
                style={{ background: "#2a3942", color: "#e9edef" }}
                value={memberEmail}
                onChange={(e) => setMemberEmail(e.target.value)}
                onKeyDown={handleEmailKeyPress}
              />
              <button
                data-testid="add-member-email-button"
                onClick={addMemberEmail}
                className="px-3 py-2 rounded-lg"
                style={{ background: "#00a884", color: "#fff" }}
              >
                <Plus size={18} />
              </button>
            </div>
            {memberEmails.length > 0 && (
              <div className="mt-2 space-y-1.5">
                {memberEmails.map((email) => (
                  <div
                    key={email}
                    className="flex items-center justify-between px-3 py-2 rounded-lg"
                    style={{ background: "#2a3942" }}
                  >
                    <span
                      className="text-xs flex items-center gap-1.5"
                      style={{ color: "#e9edef" }}
                    >
                      <Mail size={12} style={{ color: "#8696a0" }} />
                      {email}
                    </span>
                    <button
                      onClick={() => removeMemberEmail(email)}
                      style={{ color: "#ef4444" }}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div
          className="flex justify-end gap-3 px-5 py-4"
          style={{ borderTop: "1px solid #2a3942" }}
        >
          <button
            data-testid="cancel-create-group"
            onClick={close}
            className="px-4 py-2 rounded-lg text-sm"
            style={{ background: "#2a3942", color: "#8696a0" }}
          >
            Cancel
          </button>
          <button
            data-testid="submit-create-group"
            onClick={handleCreate}
            disabled={loading || !name.trim()}
            className="px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
            style={{ background: "#00a884", color: "#fff" }}
          >
            {loading ? "Creating..." : "Create Group"}
          </button>
        </div>
      </div>
    </div>
  );
}
