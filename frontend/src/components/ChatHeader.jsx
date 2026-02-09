import { useState, useEffect } from "react";
import AddMembersModal from "./AddMembersModal";

export default function ChatHeader({ group }) {
  const [showAddMembers, setShowAddMembers] = useState(false);
  const [members, setMembers] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(false);

  // ✅ Load group members
  async function loadMembers() {
    const token = localStorage.getItem("token");
    if (!token || !group?.id) return;

    setLoadingMembers(true);
    try {
      const res = await fetch(
        `http://localhost:8001/groups/${group.id}/members`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (res.ok) {
        const data = await res.json();
        setMembers(data.members || []);
      }
    } catch (err) {
      console.error("Failed to load members:", err);
    } finally {
      setLoadingMembers(false);
    }
  }

  useEffect(() => {
    loadMembers();
  }, [group?.id]);

  function handleMembersAdded() {
    loadMembers();
  }

  return (
    <>
      <div className="h-16 flex items-center justify-between px-4 bg-[#f0f2f5] border-b">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-full bg-gray-300 flex items-center justify-center text-xl">
            {group.avatar || "👥"}
          </div>

          <div>
            <p className="font-semibold">{group.name}</p>
            <p className="text-xs text-gray-500">
              Agents: {group.agents?.length || 0} | Members:{" "}
              {loadingMembers ? "..." : members.length}
            </p>
          </div>
        </div>

        {/* ✅ Add Members Button */}
        <button
          onClick={() => setShowAddMembers(true)}
          className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600 text-sm"
          title="Add members to this group"
        >
          + Add Members
        </button>
      </div>

      {/* ✅ Add Members Modal */}
      {showAddMembers && (
        <AddMembersModal
          groupId={group.id}
          close={() => setShowAddMembers(false)}
          onMembersAdded={handleMembersAdded}
        />
      )}
    </>
  );
}
