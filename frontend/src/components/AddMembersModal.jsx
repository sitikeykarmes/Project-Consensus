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
    <div className="fixed inset-0 flex justify-center items-center z-50" style={{ background: "rgba(0,0,0,0.6)" }}>
      <div
        data-testid="add-members-modal"
        className="w-[440px] max-h-[85vh] overflow-y-auto rounded-xl shadow-2xl"
        style={{ background: "#202c33", border: "1px solid #2a3942" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid #2a3942" }}>
          <h2 className="text-base font-semibold" style={{ color: "#e9edef" }}>Add Members</h2>
          <button onClick={close} className="p-1 rounded-lg" style={{ color: "#8696a0" }}>
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4">
          {/* Email Input */}
          <div className="flex gap-2 mb-3">
            <input
              data-testid="add-member-email-input"
              type="email"
              className="flex-1 px-4 py-2.5 rounded-lg text-sm focus:outline-none"
              placeholder="Enter member email..."
              style={{ background: "#2a3942", color: "#e9edef" }}
              value={memberEmail}
              onChange={(e) => setMemberEmail(e.target.value)}
              onKeyDown={handleEmailKeyPress}
              disabled={loading}
            />
            <button
              data-testid="add-email-btn"
              onClick={addMemberEmail}
              disabled={loading}
              className="px-3 py-2 rounded-lg disabled:opacity-50"
              style={{ background: "#00a884", color: "#fff" }}
            >
              <Plus size={18} />
            </button>
          </div>

          {/* Email Tags */}
          {memberEmails.length > 0 && (
            <div className="space-y-1.5 mb-4">
              <p className="text-xs font-medium" style={{ color: "#8696a0" }}>Members to add:</p>
              {memberEmails.map((email) => (
                <div key={email} className="flex items-center justify-between px-3 py-2 rounded-lg" style={{ background: "#2a3942" }}>
                  <span className="text-xs flex items-center gap-1.5" style={{ color: "#e9edef" }}>
                    <Mail size={12} style={{ color: "#8696a0" }} />
                    {email}
                  </span>
                  <button onClick={() => removeMemberEmail(email)} disabled={loading} style={{ color: "#ef4444" }}>
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-5 py-4" style={{ borderTop: "1px solid #2a3942" }}>
          <button
            onClick={close}
            disabled={loading}
            className="px-4 py-2 rounded-lg text-sm"
            style={{ background: "#2a3942", color: "#8696a0" }}
          >
            Cancel
          </button>
          <button
            data-testid="submit-add-members"
            onClick={handleAddMembers}
            disabled={loading || memberEmails.length === 0}
            className="px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
            style={{ background: "#00a884", color: "#fff" }}
          >
            {loading ? "Adding..." : "Add Members"}
          </button>
        </div>
      </div>
    </div>
  );
}
