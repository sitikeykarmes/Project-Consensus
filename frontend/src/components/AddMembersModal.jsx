import { useState } from "react";
import { X, Plus, Mail } from "lucide-react";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "";

export default function AddMembersModal({ groupId, close, onMembersAdded }) {
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

  async function handleAddMembers() {
    if (memberEmails.length === 0) {
      alert("Please add at least one email");
      return;
    }
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Login required");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/api/groups/${groupId}/add-members`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ member_emails: memberEmails }),
      });

      const data = await res.json();
      if (!res.ok) {
        alert("Failed: " + (data.detail || "Unknown error"));
        setLoading(false);
        return;
      }

      let message = "";
      if (data.added_members && data.added_members.length > 0) {
        message += `Successfully added ${data.added_members.length} member(s)\n`;
      }
      if (data.failed_members && data.failed_members.length > 0) {
        message += `\nFailed to add:\n`;
        data.failed_members.forEach((fail) => {
          message += `- ${fail.email}: ${fail.reason}\n`;
        });
      }
      alert(message || "Members added successfully!");

      if (onMembersAdded) onMembersAdded();
      close();
    } catch (err) {
      console.error(err);
      alert("Server error");
    }
    setLoading(false);
  }

  return (
    <div className="fixed inset-0 flex justify-center items-center z-50" style={{ background: "rgba(0,0,0,0.4)", backdropFilter: "blur(4px)", WebkitBackdropFilter: "blur(4px)" }}>
      <div
        data-testid="add-members-modal"
        className="w-[440px] max-h-[85vh] overflow-y-auto rounded-2xl shadow-2xl"
        style={{ 
          background: "rgba(20, 20, 20, 0.85)", 
          border: "1px solid rgba(255, 255, 255, 0.12)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)"
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid var(--border)" }}>
          <h2 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>Add Members</h2>
          <button onClick={close} className="p-1 rounded-lg transition-colors hover:bg-[rgba(255,255,255,0.1)]" style={{ color: "var(--text-secondary)" }}>
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4">
          {/* Email Input */}
          <div className="flex gap-2 mb-3">
            <input
              data-testid="add-member-email-input"
              type="email"
              className="flex-1 px-4 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-[var(--accent)] transition-all"
              placeholder="Enter member email..."
              style={{ background: "rgba(255,255,255,0.05)", color: "var(--text-primary)", border: "1px solid var(--border)" }}
              value={memberEmail}
              onChange={(e) => setMemberEmail(e.target.value)}
              onKeyDown={handleEmailKeyPress}
              disabled={loading}
            />
            <button
              data-testid="add-email-btn"
              onClick={addMemberEmail}
              disabled={loading}
              className="px-3 py-2 rounded-lg transition-transform active:scale-95 disabled:opacity-50"
              style={{ background: "var(--accent)", color: "var(--bg-app)" }}
            >
              <Plus size={18} />
            </button>
          </div>

          {/* Email Tags */}
          {memberEmails.length > 0 && (
            <div className="space-y-1.5 mb-4">
              <p className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Members to add:</p>
              {memberEmails.map((email) => (
                <div key={email} className="flex items-center justify-between px-3 py-2 rounded-lg" style={{ background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)" }}>
                  <span className="text-xs flex items-center gap-1.5" style={{ color: "var(--text-primary)" }}>
                    <Mail size={12} style={{ color: "var(--text-secondary)" }} />
                    {email}
                  </span>
                  <button onClick={() => removeMemberEmail(email)} disabled={loading} className="transition-colors hover:text-red-400" style={{ color: "#ef4444" }}>
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-5 py-4" style={{ borderTop: "1px solid var(--border)" }}>
          <button
            onClick={close}
            disabled={loading}
            className="px-4 py-2 rounded-lg text-sm transition-colors hover:bg-[rgba(255,255,255,0.1)]"
            style={{ background: "transparent", color: "var(--text-secondary)", border: "1px solid var(--border)" }}
          >
            Cancel
          </button>
          <button
            data-testid="submit-add-members"
            onClick={handleAddMembers}
            disabled={loading || memberEmails.length === 0}
            className="px-5 py-2 rounded-lg text-sm font-medium transition-transform active:scale-95 disabled:opacity-50 disabled:scale-100"
            style={{ background: "var(--accent)", color: "var(--bg-app)" }}
          >
            {loading ? "Adding..." : "Add Members"}
          </button>
        </div>
      </div>
    </div>
  );
}
