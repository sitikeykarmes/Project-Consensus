export default function ChatHeader({ group }) {
  return (
    <div className="h-16 flex items-center justify-between px-4 bg-[#f0f2f5] border-b">
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-full bg-gray-300 flex items-center justify-center text-xl">
          {group.avatar}
        </div>

        <div>
          <p className="font-semibold">{group.name}</p>
          <p className="text-xs text-gray-500">Agents: {group.agents.length}</p>
        </div>
      </div>
    </div>
  );
}
