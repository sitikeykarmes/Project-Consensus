const BASE_URL = import.meta.env.VITE_BACKEND_URL || "";

export async function fetchGroups(token) {
  const res = await fetch(`${BASE_URL}/api/groups/my`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const err = await res.json();
    console.error("Fetch Groups Error:", err);
    return { groups: [] };
  }

  return res.json();
}

export async function fetchAgents() {
  const res = await fetch(`${BASE_URL}/api/agents`);
  return res.json();
}

export async function createGroup(groupData) {
  const res = await fetch(`${BASE_URL}/api/groups/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(groupData),
  });

  return res.json();
}

export function getWsUrl(roomId, token) {
  const backendUrl = BASE_URL || window.location.origin;
  const wsProtocol = backendUrl.startsWith("https") ? "wss" : "ws";
  const host = backendUrl.replace(/^https?:\/\//, "");
  return `${wsProtocol}://${host}/api/ws/${roomId}?token=${token}`;
}
