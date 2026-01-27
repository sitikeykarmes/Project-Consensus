export default function MessageBubble({ sender, content, type }) {
  const isUser = type === "user";
  const isAgent = type === "agent";
  const isConsensus = type === "consensus";

  let bgColor = "bg-slate-700";
  if (isUser) bgColor = "bg-blue-600";
  if (isAgent) bgColor = "bg-purple-600";
  if (isConsensus) bgColor = "bg-green-600";

  return (
    <div className={`max-w-xl p-3 rounded-xl mb-2 ${bgColor}`}>
      <div className="text-xs opacity-70 mb-1">{sender}</div>
      <div className="text-sm whitespace-pre-wrap">{content}</div>
    </div>
  );
}
