import { useState } from "react";
import { X, Plus, Users, Mail } from "lucide-react";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "";

export default function CreateGroupModal({ close, reloadGroups }) {
  const [name, setName] = useState("");
  const [memberEmail, setMemberEmail] = useState("");
  const [memberEmails, setMemberEmails] = useState([]);
  const [loading, setLoading] = useState(false);

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
          agents: ["all"],
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
      style={{ background: "rgba(0,0,0,0.4)", backdropFilter: "blur(4px)", WebkitBackdropFilter: "blur(4px)" }}
    >
      <div
        data-testid="create-group-modal"
        className="w-[480px] max-h-[85vh] overflow-y-auto rounded-2xl shadow-2xl"
        style={{ 
          background: "rgba(20, 20, 20, 0.85)", 
          border: "1px solid rgba(255, 255, 255, 0.12)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)"
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5 py-4"
          style={{ borderBottom: "1px solid var(--border)" }}
        >
          <h2 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
            Create New Group
          </h2>
          <button
            onClick={close}
            className="p-1 rounded-lg transition-colors hover:bg-[rgba(255,255,255,0.1)]"
            style={{ color: "var(--text-secondary)" }}
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Group Name */}
          <div>
            <label
              className="text-xs font-medium mb-1.5 block"
              style={{ color: "var(--text-secondary)" }}
            >
              Group Name
            </label>
            <input
              data-testid="group-name-input"
              className="w-full px-4 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-all"
              placeholder="Enter group name..."
              style={{
                background: "rgba(255,255,255,0.05)",
                color: "var(--text-primary)",
                border: "1px solid var(--border)",
              }}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>



          {/* Members */}
          <div>
            <label
              className="text-xs font-medium mb-2 flex items-center gap-1.5"
              style={{ color: "var(--text-secondary)" }}
            >
              <Users size={14} /> Invite Members (Optional)
            </label>
            <div className="flex gap-2">
              <input
                data-testid="member-email-input"
                type="email"
                className="flex-1 px-4 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-all"
                placeholder="Enter email..."
                style={{ 
                  background: "rgba(255,255,255,0.05)", 
                  color: "var(--text-primary)",
                  border: "1px solid var(--border)"
                }}
                value={memberEmail}
                onChange={(e) => setMemberEmail(e.target.value)}
                onKeyDown={handleEmailKeyPress}
              />
              <button
                data-testid="add-member-email-button"
                onClick={addMemberEmail}
                className="px-3 py-2 rounded-lg transition-transform active:scale-95"
                style={{ background: "var(--accent)", color: "var(--bg-app)" }}
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
                    style={{ background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)" }}
                  >
                    <span
                      className="text-xs flex items-center gap-1.5"
                      style={{ color: "var(--text-primary)" }}
                    >
                      <Mail size={12} style={{ color: "var(--text-secondary)" }} />
                      {email}
                    </span>
                    <button
                      onClick={() => removeMemberEmail(email)}
                      className="transition-colors hover:text-red-400"
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
          style={{ borderTop: "1px solid var(--border)" }}
        >
          <button
            data-testid="cancel-create-group"
            onClick={close}
            className="px-4 py-2 rounded-lg text-sm transition-colors hover:bg-[rgba(255,255,255,0.1)]"
            style={{ background: "transparent", color: "var(--text-secondary)", border: "1px solid var(--border)" }}
          >
            Cancel
          </button>
          <button
            data-testid="submit-create-group"
            onClick={handleCreate}
            disabled={loading || !name.trim()}
            className="px-5 py-2 rounded-lg text-sm font-medium transition-transform active:scale-95 disabled:opacity-50 disabled:scale-100"
            style={{ background: "var(--accent)", color: "var(--bg-app)" }}
          >
            {loading ? "Creating..." : "Create Group"}
          </button>
        </div>
      </div>
    </div>
  );
}
