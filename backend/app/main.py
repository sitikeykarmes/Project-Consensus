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
orchestrator = None
try:
    # Explicitly verify API keys are loaded
    groq_key = os.getenv("GROQ_API_KEY")
    groq_key_1 = os.getenv("GROQ_API_KEY_1")
    
    if groq_key and groq_key_1:
        print(f"✅ API keys loaded successfully")
        orchestrator = Orchestrator()
        print(f"✅ Orchestrator initialized successfully")
    else:
        print(f"⚠️ Warning: API keys not found in environment")
        print(f"   GROQ_API_KEY: {'Found' if groq_key else 'NOT FOUND'}")
        print(f"   GROQ_API_KEY_1: {'Found' if groq_key_1 else 'NOT FOUND'}")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize orchestrator: {e}")
    print(f"   The chat interface will work, but AI agents won't respond")
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
    """
    WhatsApp-like real-time group chat WebSocket
    Supports:
    - User messages
    - Multi-agent responses
    - Consensus + Mode display
    """

    await manager.connect(websocket, room_id, user_name)

    # Notify room user joined
    await manager.broadcast_to_room({
        "type": "user_joined",
        "user_name": user_name,
        "online_users": manager.get_room_users(room_id),
        "timestamp": datetime.now().isoformat()
    }, room_id)

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("message", "").strip()

            if not user_message:
                continue

            # Update group last message
            if room_id in groups_db:
                groups_db[room_id]["last_message"] = user_message[:50]
                groups_db[room_id]["last_message_time"] = datetime.now().isoformat()

            # Broadcast user message instantly
            await manager.broadcast_to_room({
                "type": "user_message",
                "user_name": user_name,
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            }, room_id)

            # -------------------------------------------------------
            # ✅ MULTI-AGENT RESPONSE LOGIC
            # -------------------------------------------------------

            if orchestrator and room_id in groups_db:

                group = groups_db[room_id]

                # If no agents in this group → skip AI
                if not group["agents"]:
                    continue

                print(f"\n🤖 Agents active in {room_id}: {group['agents']}")

                try:
                    # Run orchestrator pipeline
                    result = orchestrator.execute_query(user_message)

                    mode_used = result["mode_used"]
                    agent_responses = result["agent_responses"]
                    final_answer = result["final_answer"]

                    # ✅ Broadcast mode info first
                    await manager.broadcast_to_room({
                        "type": "system",
                        "content": f"⚙️ Mode Selected: {mode_used.upper()}",
                        "timestamp": datetime.now().isoformat()
                    }, room_id)

                    # -------------------------------------------------------
                    # ✅ STREAM EACH AGENT RESPONSE
                    # -------------------------------------------------------

                    # Correct mapping based on your backend agent naming
                    agent_id_map = {
                        "Agent 1 (Agent 1)": "agent_research",
                        "Lead Agent (Agent 1)": "agent_research",
                        "Generator (Agent 1)": "agent_research",

                        "Agent 2 (Agent 2)": "agent_analysis",
                        "Supplementer (Agent 2)": "agent_analysis",
                        "Critic (Agent 2)": "agent_analysis",

                        "Agent 3 (Agent 3)": "agent_synthesis",
                    }

                    for response in agent_responses:
                        agent_name = response["agent_name"]
                        content = response["content"]

                        agent_id = agent_id_map.get(agent_name)

                        # Only send if agent is actually inside this group
                        if agent_id and agent_id in group["agents"]:

                            await manager.broadcast_to_room({
                                "type": "agent_response",
                                "agent_id": agent_id,
                                "agent_name": agent_name,
                                "content": f"[Mode: {mode_used}] \n\n{content}",
                                "timestamp": datetime.now().isoformat()
                            }, room_id)

                    # -------------------------------------------------------
                    # ✅ FINAL CONSENSUS MESSAGE
                    # -------------------------------------------------------

                    await manager.broadcast_to_room({
                        "type": "consensus",
                        "content": f"✅ FINAL CONSENSUS ({mode_used.upper()} MODE):\n\n{final_answer}",
                        "mode_used": mode_used,
                        "timestamp": datetime.now().isoformat()
                    }, room_id)

                except Exception as e:
                    print("❌ Error running orchestrator:", e)

                    await manager.broadcast_to_room({
                        "type": "error",
                        "content": "⚠️ AI Agents failed to respond.",
                        "timestamp": datetime.now().isoformat()
                    }, room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

        await manager.broadcast_to_room({
            "type": "user_left",
            "user_name": user_name,
            "online_users": manager.get_room_users(room_id),
            "timestamp": datetime.now().isoformat()
        }, room_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)