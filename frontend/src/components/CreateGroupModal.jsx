import { useEffect, useState } from "react";
import { fetchAgents } from "../api/ChatApi";

export default function CreateGroupModal({ close, reloadGroups }) {
  const [name, setName] = useState("");
  const [agents, setAgents] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);

  // ✅ Member email management
  const [memberEmail, setMemberEmail] = useState("");
  const [memberEmails, setMemberEmails] = useState([]);

  // ✅ Load available AI agents
  useEffect(() => {
    async function loadAgents() {
      try {
        const data = await fetchAgents();
        setAgents(data.agents);
      } catch (err) {
        alert("Failed to load agents");
      }
    }

    loadAgents();
  }, []);

  // ✅ Toggle agent selection
  function toggleAgent(agentId) {
    if (selectedAgents.includes(agentId)) {
      setSelectedAgents(selectedAgents.filter((a) => a !== agentId));
    } else {
      setSelectedAgents([...selectedAgents, agentId]);
    }
  }

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

  // ✅ Create group with JWT token
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

    try {
      const res = await fetch("http://localhost:8001/groups/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },

        // ✅ Send name + selected agents + member emails
        body: JSON.stringify({
          name: name,
          agents: selectedAgents,
          member_emails: memberEmails,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        alert("❌ Failed: " + (data.detail || "Unknown error"));
        return;
      }

      // ✅ Show results
      let message = "✅ Group Created Successfully!";

      if (data.added_members && data.added_members.length > 0) {
        message += `\n\n✅ Added ${data.added_members.length} member(s)`;
      }

      if (data.failed_members && data.failed_members.length > 0) {
        message += `\n\n⚠️ Failed to add:\n`;
        data.failed_members.forEach((fail) => {
          message += `- ${fail.email}: ${fail.reason}\n`;
        });
      }

      alert(message);

      reloadGroups();
      close();
    } catch (err) {
      console.error(err);
      alert("Server error");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50">
      <div className="bg-white w-[500px] max-h-[90vh] overflow-y-auto rounded-xl shadow-lg p-6">
        <h2 className="text-lg font-bold mb-4">Create Group</h2>

        {/* ✅ Group Name */}
        <input
          className="w-full border p-2 rounded mb-4"
          placeholder="Group Name..."
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {/* ✅ Agent Selection */}
        <p className="font-semibold mb-2">Select AI Agents:</p>

        <div className="space-y-2 mb-4">
          {agents.map((agent) => (
            <label
              key={agent.id}
              className="flex items-center gap-2 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedAgents.includes(agent.id)}
                onChange={() => toggleAgent(agent.id)}
              />

              <span>
                {agent.avatar} {agent.name}
              </span>
            </label>
          ))}
        </div>

        {/* ✅ Member Email Section */}
        <div className="border-t pt-4 mt-4">
          <p className="font-semibold mb-2">Add Members (Optional):</p>

          <div className="flex gap-2 mb-3">
            <input
              type="email"
              className="flex-1 border p-2 rounded"
              placeholder="Enter member email..."
              value={memberEmail}
              onChange={(e) => setMemberEmail(e.target.value)}
              onKeyPress={handleEmailKeyPress}
            />
            <button
              onClick={addMemberEmail}
              className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600"
            >
              Add
            </button>
          </div>

          {/* ✅ Display added emails */}
          {memberEmails.length > 0 && (
            <div className="space-y-1 mb-3">
              <p className="text-sm text-gray-600">Members to invite:</p>
              {memberEmails.map((email) => (
                <div
                  key={email}
                  className="flex items-center justify-between bg-gray-100 px-3 py-2 rounded"
                >
                  <span className="text-sm">{email}</span>
                  <button
                    onClick={() => removeMemberEmail(email)}
                    className="text-red-500 hover:text-red-700 font-bold"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ✅ Buttons */}
        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={close}
            className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
          >
            Cancel
          </button>

          <button
            onClick={handleCreate}
            className="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700"
          >
            Create
          </button>
        </div>
      </div>
    </div>
  );
}
