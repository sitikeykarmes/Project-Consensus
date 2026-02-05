const BASE_URL = "http://localhost:8001";

export async function fetchGroups() {
  const res = await fetch(`${BASE_URL}/api/groups`);
  return res.json();
}

export async function fetchAgents() {
  const res = await fetch(`${BASE_URL}/api/agents`);
  return res.json();
}

export async function createGroup(groupData) {
  const res = await fetch(`${BASE_URL}/api/groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(groupData),
  });

  return res.json();
}
