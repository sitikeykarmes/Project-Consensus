export default function Sidebar({ users, agents }) {
  return (
    <div className="w-64 bg-slate-900 border-r border-slate-700 p-4">
      <h2 className="text-lg font-bold mb-3">Group Members</h2>

      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-2">Users</h3>
        {users.map((u, i) => (
          <div key={i} className="text-sm text-slate-300">
            👤 {u}
          </div>
        ))}
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-2">AI Agents</h3>
        {agents.map((a, i) => (
          <div key={i} className="text-sm text-purple-400">
            🤖 {a}
          </div>
        ))}
      </div>
    </div>
  );
}
