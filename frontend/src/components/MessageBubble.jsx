export default function MessageBubble({ msg }) {
  const isUser = msg.type === "user_message";
  const isAgent = msg.type === "agent_response";
  const isConsensus = msg.type === "consensus";
  const isSystem = msg.type === "system";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[65%] px-4 py-2 rounded-xl text-sm shadow-sm whitespace-pre-line
        ${
          isUser
            ? "bg-[#d9fdd3]"
            : isAgent
              ? "bg-white border-l-4 border-blue-500"
              : isConsensus
                ? "bg-yellow-100 border-l-4 border-green-600"
                : "bg-gray-200 italic"
        }`}
      >
        {isAgent && <p className="font-bold text-xs mb-1">{msg.agent_name}</p>}

        <p>{msg.content}</p>
      </div>
    </div>
  );
}
