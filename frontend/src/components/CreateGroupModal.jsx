import { useEffect, useState } from "react";
import { fetchAgents } from "../api/ChatApi";

export default function CreateGroupModal({ close, reloadGroups }) {
  const [name, setName] = useState("");
  const [agents, setAgents] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);

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

        // ✅ Send name + selected agents
        body: JSON.stringify({
          name: name,
          agents: selectedAgents,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        alert("❌ Failed: " + (data.detail || "Unknown error"));
        return;
      }

      alert("✅ Group Created Successfully!");

      reloadGroups();
      close();
    } catch (err) {
      console.error(err);
      alert("Server error");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center">
      <div className="bg-white w-[400px] rounded-xl shadow-lg p-6">
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

        <div className="space-y-2">
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

        {/* ✅ Buttons */}
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={close} className="px-4 py-2 rounded bg-gray-200">
            Cancel
          </button>

          <button
            onClick={handleCreate}
            className="px-4 py-2 rounded bg-green-600 text-white"
          >
            Create
          </button>
        </div>
      </div>
    </div>
  );
}
