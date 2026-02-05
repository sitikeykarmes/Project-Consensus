import { useEffect, useState } from "react";
import { fetchAgents, createGroup } from "../api/ChatApi";

export default function CreateGroupModal({ close, reloadGroups }) {
  const [name, setName] = useState("");
  const [agents, setAgents] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);

  useEffect(() => {
    async function loadAgents() {
      const data = await fetchAgents();
      setAgents(data.agents);
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

  async function handleCreate() {
    if (!name.trim()) return;

    await createGroup({
      name,
      avatar: "👥",
      agents: selectedAgents,
    });

    reloadGroups();
    close();
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center">
      <div className="bg-white w-[400px] rounded-xl shadow-lg p-6">
        <h2 className="text-lg font-bold mb-4">Create Group</h2>

        {/* Group Name */}
        <input
          className="w-full border p-2 rounded mb-4"
          placeholder="Group Name..."
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {/* Agent Selection */}
        <p className="font-semibold mb-2">Select Agents:</p>

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
              {agent.avatar} {agent.name}
            </label>
          ))}
        </div>

        {/* Buttons */}
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
