#backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import QueryRequest, ConsensusOutput, Group, CreateGroupRequest, AddMemberRequest
from app.agents.orchestrator import Orchestrator
from typing import Dict, List
import json
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="WhatsApp-like Chat API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for groups
groups_db: Dict[str, dict] = {}

# Available AI agents
AVAILABLE_AGENTS = [
    {"id": "agent_research", "name": "Agent 1", "type": "agent", "avatar": "🔍"},
    {"id": "agent_analysis", "name": "Agent 2", "type": "agent", "avatar": "📊"},
    {"id": "agent_synthesis", "name": "Agent 3", "type": "agent", "avatar": "🧠"},
]

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[Dict]] = {}  # room_id -> [{websocket, user_name}]
    
    async def connect(self, websocket: WebSocket, room_id: str, user_name: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append({"websocket": websocket, "user_name": user_name})
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                conn for conn in self.active_connections[room_id] 
                if conn["websocket"] != websocket
            ]
    
    async def broadcast_to_room(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection["websocket"].send_json(message)
                except:
                    pass
    
    def get_room_users(self, room_id: str) -> List[str]:
        if room_id not in self.active_connections:
            return []
        return [conn["user_name"] for conn in self.active_connections[room_id]]

manager = ConnectionManager()

# Initialize orchestrator (optional, for AI agents)
try:
    orchestrator = Orchestrator()
except Exception as e:
    print(f"Warning: Could not initialize orchestrator: {e}")
    orchestrator = None

# Initialize default groups
def initialize_default_groups():
    if not groups_db:
        # Create a default general group
        default_group = {
            "id": "group_general",
            "name": "General Chat",
            "avatar": "💬",
            "members": [],
            "agents": ["agent_research"],
            "created_at": datetime.now().isoformat(),
            "last_message": "Welcome to the group!",
            "last_message_time": datetime.now().isoformat()
        }
        groups_db["group_general"] = default_group

initialize_default_groups()

@app.get("/")
def read_root():
    return {"message": "WhatsApp-like Chat API is running", "status": "active"}

@app.get("/api/groups")
def get_groups():
    """Get all groups"""
    return {"groups": list(groups_db.values())}

@app.post("/api/groups")
def create_group(request: CreateGroupRequest):
    """Create a new group"""
    group_id = f"group_{uuid.uuid4().hex[:8]}"
    
    new_group = {
        "id": group_id,
        "name": request.name,
        "avatar": request.avatar or "👥",
        "members": request.members or [],
        "agents": request.agents or [],
        "created_at": datetime.now().isoformat(),
        "last_message": "",
        "last_message_time": datetime.now().isoformat()
    }
    
    groups_db[group_id] = new_group
    return {"success": True, "group": new_group}

@app.get("/api/groups/{group_id}")
def get_group(group_id: str):
    """Get group details"""
    if group_id not in groups_db:
        raise HTTPException(status_code=404, detail="Group not found")
    return groups_db[group_id]

@app.post("/api/groups/{group_id}/members")
def add_member(group_id: str, request: AddMemberRequest):
    """Add member or agent to group"""
    if group_id not in groups_db:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = groups_db[group_id]
    
    if request.member_type == "agent":
        if request.member_id not in group["agents"]:
            group["agents"].append(request.member_id)
    else:
        if request.member_id not in group["members"]:
            group["members"].append(request.member_id)
    
    return {"success": True, "group": group}

@app.delete("/api/groups/{group_id}/members/{member_id}")
def remove_member(group_id: str, member_id: str):
    """Remove member or agent from group"""
    if group_id not in groups_db:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = groups_db[group_id]
    
    if member_id in group["members"]:
        group["members"].remove(member_id)
    elif member_id in group["agents"]:
        group["agents"].remove(member_id)
    
    return {"success": True, "group": group}

@app.get("/api/agents")
def get_available_agents():
    """Get list of available AI agents"""
    return {"agents": AVAILABLE_AGENTS}

@app.post("/api/query", response_model=ConsensusOutput)
async def process_query(request: QueryRequest):
    """Process user query through orchestration"""
    if orchestrator:
        result = orchestrator.execute_query(request.message)
        return ConsensusOutput(
            final_answer=result["final_answer"],
            mode_used=result["mode_used"],
            agent_responses=result["agent_responses"]
        )
    else:
        return ConsensusOutput(
            final_answer="AI agents are not available at the moment.",
            mode_used="none",
            agent_responses=[]
        )

@app.websocket("/ws/{room_id}/{user_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_name: str):
    await manager.connect(websocket, room_id, user_name)
    
    # Update group's online users
    online_users = manager.get_room_users(room_id)
    
    # Notify room of new user
    await manager.broadcast_to_room({
        "type": "user_joined",
        "user_name": user_name,
        "online_users": online_users,
        "timestamp": datetime.now().isoformat()
    }, room_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Update last message in group
            if room_id in groups_db:
                groups_db[room_id]["last_message"] = message_data["message"][:50]
                groups_db[room_id]["last_message_time"] = datetime.now().isoformat()
            
            # Broadcast user message to room
            await manager.broadcast_to_room({
                "type": "user_message",
                "user_name": user_name,
                "content": message_data["message"],
                "timestamp": datetime.now().isoformat()
            }, room_id)
            
            # Check if any agents are in this group
            if orchestrator and room_id in groups_db:
                group = groups_db[room_id]
                if group["agents"]:
                    # Process through orchestrator
                    try:
                        result = orchestrator.execute_query(message_data["message"])
                        
                        # Stream agent responses for agents in this group
                        for agent_response in result["agent_responses"]:
                            # Map agent names to IDs
                            agent_id_map = {
                                "Research Agent": "agent_research",
                                "Analysis Agent": "agent_analysis",
                                "Synthesis Agent": "agent_synthesis"
                            }
                            
                            agent_id = agent_id_map.get(agent_response["agent_name"])
                            
                            if agent_id and agent_id in group["agents"]:
                                await manager.broadcast_to_room({
                                    "type": "agent_response",
                                    "agent_id": agent_id,
                                    "agent_name": agent_response["agent_name"],
                                    "content": agent_response["content"],
                                    "mode": agent_response["mode"],
                                    "timestamp": datetime.now().isoformat()
                                }, room_id)
                        
                        # Send final consensus if agents are present
                        if result["agent_responses"]:
                            await manager.broadcast_to_room({
                                "type": "consensus",
                                "content": result["final_answer"],
                                "mode_used": result["mode_used"],
                                "timestamp": datetime.now().isoformat()
                            }, room_id)
                    except Exception as e:
                        print(f"Error processing agent query: {e}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        online_users = manager.get_room_users(room_id)
        await manager.broadcast_to_room({
            "type": "user_left",
            "user_name": user_name,
            "online_users": online_users,
            "timestamp": datetime.now().isoformat()
        }, room_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)