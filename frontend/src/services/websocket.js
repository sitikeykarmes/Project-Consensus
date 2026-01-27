let socket = null;

export function connectWebSocket(roomId, userName, onMessage) {
  const url = `ws://localhost:8000/ws/${roomId}/${userName}`;
  socket = new WebSocket(url);

  socket.onopen = () => {
    console.log("✅ WebSocket connected");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  socket.onclose = () => {
    console.log("❌ WebSocket disconnected");
  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
  };
}

export function sendMessage(message) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ message }));
  }
}
