import { useState } from "react";

export default function AddMembersModal({ groupId, close, onMembersAdded }) {
  const [memberEmail, setMemberEmail] = useState("");
  const [memberEmails, setMemberEmails] = useState([]);
  const [loading, setLoading] = useState(false);

  // ✅ Add member email to list
  function addMemberEmail() {
    const email = memberEmail.trim().toLowerCase();

    if (!email) {
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert("Please enter a valid email address");
      return;
    }

    // Check for duplicates
    if (memberEmails.includes(email)) {
      alert("Email already added");
      return;
    }

    setMemberEmails([...memberEmails, email]);
    setMemberEmail("");
  }

  // ✅ Remove member email from list
  function removeMemberEmail(email) {
    setMemberEmails(memberEmails.filter((e) => e !== email));
  }

  // ✅ Handle Enter key in email input
  function handleEmailKeyPress(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      addMemberEmail();
    }
  }

  // ✅ Add members to group
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
      const res = await fetch(
        `http://localhost:8001/groups/${groupId}/add-members`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            member_emails: memberEmails,
          }),
        },
      );

      const data = await res.json();

      if (!res.ok) {
        alert("❌ Failed: " + (data.detail || "Unknown error"));
        setLoading(false);
        return;
      }

      // ✅ Show results
      let message = "";

      if (data.added_members && data.added_members.length > 0) {
        message += `✅ Successfully added ${data.added_members.length} member(s)\n`;
        data.added_members.forEach((member) => {
          message += `- ${member.email}\n`;
        });
      }

      if (data.failed_members && data.failed_members.length > 0) {
        message += `\n⚠️ Failed to add:\n`;
        data.failed_members.forEach((fail) => {
          message += `- ${fail.email}: ${fail.reason}\n`;
        });
      }

      alert(message || "✅ Members added successfully!");

      if (onMembersAdded) {
        onMembersAdded();
      }

      close();
    } catch (err) {
      console.error(err);
      alert("Server error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50">
      <div className="bg-white w-[450px] max-h-[90vh] overflow-y-auto rounded-xl shadow-lg p-6">
        <h2 className="text-lg font-bold mb-4">Add Members to Group</h2>

        {/* ✅ Email Input */}
        <div className="flex gap-2 mb-3">
          <input
            type="email"
            className="flex-1 border p-2 rounded"
            placeholder="Enter member email..."
            value={memberEmail}
            onChange={(e) => setMemberEmail(e.target.value)}
            onKeyPress={handleEmailKeyPress}
            disabled={loading}
          />
          <button
            onClick={addMemberEmail}
            disabled={loading}
            className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600 disabled:bg-gray-400"
          >
            Add
          </button>
        </div>

        {/* ✅ Display added emails */}
        {memberEmails.length > 0 && (
          <div className="space-y-1 mb-4">
            <p className="text-sm text-gray-600 font-semibold">
              Members to add:
            </p>
            {memberEmails.map((email) => (
              <div
                key={email}
                className="flex items-center justify-between bg-gray-100 px-3 py-2 rounded"
              >
                <span className="text-sm">{email}</span>
                <button
                  onClick={() => removeMemberEmail(email)}
                  disabled={loading}
                  className="text-red-500 hover:text-red-700 font-bold disabled:text-gray-400"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* ✅ Buttons */}
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={close}
            disabled={loading}
            className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100"
          >
            Cancel
          </button>

          <button
            onClick={handleAddMembers}
            disabled={loading || memberEmails.length === 0}
            className="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 disabled:bg-gray-400"
          >
            {loading ? "Adding..." : "Add Members"}
          </button>
        </div>
      </div>
    </div>
  );
}
