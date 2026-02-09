export default function MessageBubble({ msg, currentUserId }) {
  // ✅ Check if this message is from the current logged-in user
  const isCurrentUser = msg.type === "user" && msg.sender_id === currentUserId;
  const isAgent = msg.type === "agent";
  const isSystem = msg.type === "system";

  // ✅ Label formatting
  function getSenderLabel() {
    if (isCurrentUser) return "You";

    if (msg.type === "user") return msg.sender_name || "User";

    if (isAgent) return msg.sender_name || "Agent";

    if (isSystem) {
      if (msg.sender_name === "Consensus") return "🤝 Consensus";
      return msg.sender_name || "System";
    }

    return "";
  }

  return (
    <div className={`flex ${isCurrentUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[65%] px-4 py-2 rounded-xl text-sm shadow-sm whitespace-pre-line
        ${
          isCurrentUser
            ? "bg-[#d9fdd3]"
            : isAgent
              ? "bg-white border-l-4 border-blue-500"
              : "bg-yellow-100 border-l-4 border-green-600 italic"
        }`}
      >
        {/* ✅ Always show sender name */}
        <p className="font-bold text-xs mb-1 text-gray-600">
          {getSenderLabel()}
        </p>

        {/* Message Content */}
        <p>{msg.content}</p>
      </div>
    </div>
  );
}
