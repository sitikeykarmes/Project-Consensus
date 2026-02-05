import { useState } from "react";
import Sidebar from "../components/Sidebar";
import ChatRoom from "../components/ChatRoom";

export default function Home() {
  const [selectedGroup, setSelectedGroup] = useState(null);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <Sidebar onSelectGroup={setSelectedGroup} />

      {/* Chat Window */}
      <div className="flex-1">
        {selectedGroup ? (
          <ChatRoom group={selectedGroup} />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500 text-lg">
            Select a group to start chatting 💬
          </div>
        )}
      </div>
    </div>
  );
}
