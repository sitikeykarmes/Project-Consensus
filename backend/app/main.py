#backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import QueryRequest, ConsensusOutput
from app.agents.orchestrator import Orchestrator
from typing import Dict, List
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Project Consensus API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
    
    async def broadcast_to_room(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()
orchestrator = Orchestrator()

@app.get("/")
def read_root():
    return {"message": "Project Consensus API is running", "status": "active"}

@app.post("/api/query", response_model=ConsensusOutput)
async def process_query(request: QueryRequest):
    """Process user query through orchestration"""
    result = orchestrator.execute_query(request.message)
    
    return ConsensusOutput(
        final_answer=result["final_answer"],
        mode_used=result["mode_used"],
        agent_responses=result["agent_responses"]
    )

@app.websocket("/ws/{room_id}/{user_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_name: str):
    await manager.connect(websocket, room_id)
    
    # Notify room of new user
    await manager.broadcast_to_room({
        "type": "user_joined",
        "user_name": user_name,
        "timestamp": datetime.now().isoformat()
    }, room_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Broadcast user message to room
            await manager.broadcast_to_room({
                "type": "user_message",
                "user_name": user_name,
                "content": message_data["message"],
                "timestamp": datetime.now().isoformat()
            }, room_id)
            
            # Process through orchestrator
            result = orchestrator.execute_query(message_data["message"])
            
            # Stream agent responses
            for agent_response in result["agent_responses"]:
                await manager.broadcast_to_room({
                    "type": "agent_response",
                    "agent_name": agent_response["agent_name"],
                    "content": agent_response["content"],
                    "mode": agent_response["mode"],
                    "timestamp": datetime.now().isoformat()
                }, room_id)
            
            # Send final consensus
            await manager.broadcast_to_room({
                "type": "consensus",
                "content": result["final_answer"],
                "mode_used": result["mode_used"],
                "timestamp": datetime.now().isoformat()
            }, room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast_to_room({
            "type": "user_left",
            "user_name": user_name,
            "timestamp": datetime.now().isoformat()
        }, room_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
