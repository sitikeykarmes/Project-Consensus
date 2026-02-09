import { useState } from "react";
import CreateGroupModal from "./CreateGroupModal";

export default function Sidebar({
  groups,
  activeGroup,
  setActiveGroup,
  reloadGroups,
  user,
  logout,
}) {
  const [showModal, setShowModal] = useState(false);

  return (
    <div className="w-[30%] min-w-[320px] bg-white border-r flex flex-col">
      {/* Header */}
      <div className="h-20 flex flex-col justify-center px-4 bg-[#f0f2f5] border-b">
        {/* Top Row */}
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-lg">Chats</h2>

          <button
            onClick={() => setShowModal(true)}
            className="bg-green-600 text-white px-3 py-1 rounded-lg text-sm"
          >
            + New Group
          </button>
        </div>

        {/* Logged-in User Info */}
        <div className="flex items-center justify-between mt-1">
          <p className="text-xs text-gray-600">
            Logged in as: <span className="font-semibold">{user?.email}</span>
          </p>

          <button
            onClick={logout}
            className="text-xs text-red-500 hover:underline"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Group List */}
      <div className="flex-1 overflow-y-auto">
        {groups?.length > 0 ? (
          groups.map((group) => (
            <div
              key={group.id}
              onClick={() => setActiveGroup(group)}
              className={`flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-100 ${
                activeGroup?.id === group.id ? "bg-gray-200" : ""
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-gray-300 flex items-center justify-center text-xl">
                {group.avatar || "👥"}
              </div>

              <div className="flex-1 border-b pb-2">
                <p className="font-semibold">{group.name}</p>
                <p className="text-sm text-gray-500 truncate">
                  {group.last_message || "No messages yet..."}
                </p>
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500 text-center mt-4">
            No groups yet...
          </p>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <CreateGroupModal
          close={() => setShowModal(false)}
          reloadGroups={reloadGroups}
        />
      )}
    </div>
  );
}
