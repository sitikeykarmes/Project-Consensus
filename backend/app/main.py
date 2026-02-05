# backend/app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    QueryRequest,
    ConsensusOutput,
    CreateGroupRequest,
    AddMemberRequest,
)

from app.agents.orchestrator import Orchestrator

from typing import Dict, List
import json
from datetime import datetime
import uuid
import os

from dotenv import load_dotenv
from pathlib import Path


# ------------------------------------------------------------
# ✅ Load Environment Variables
# ------------------------------------------------------------

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="WhatsApp-like Chat API")


# ------------------------------------------------------------
# ✅ Enable CORS
# ------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# ✅ In-Memory Group Storage
# ------------------------------------------------------------

groups_db: Dict[str, dict] = {}


# ------------------------------------------------------------
# ✅ Available AI Agents
# ------------------------------------------------------------

AVAILABLE_AGENTS = [
    {"id": "agent_research", "name": "Agent 1", "type": "agent", "avatar": "🔍"},
    {"id": "agent_analysis", "name": "Agent 2", "type": "agent", "avatar": "📊"},
    {"id": "agent_synthesis", "name": "Agent 3", "type": "agent", "avatar": "🧠"},
]


# ------------------------------------------------------------
# ✅ WebSocket Connection Manager
# ------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[Dict]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_name: str):
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = []

        self.active_connections[room_id].append(
            {"websocket": websocket, "user_name": user_name}
        )

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                conn
                for conn in self.active_connections[room_id]
                if conn["websocket"] != websocket
            ]

    async def broadcast_to_room(self, message: dict, room_id: str):
        if room_id not in self.active_connections:
            return

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


# ------------------------------------------------------------
# ✅ Initialize Orchestrator Safely
# ------------------------------------------------------------

orchestrator = None

try:
    groq_key_1 = os.getenv("GROQ_API_KEY_1")

    if groq_key_1:
        print("✅ GROQ API Key Loaded")
        orchestrator = Orchestrator()
        print("✅ Orchestrator Initialized Successfully")
    else:
        print("⚠️ GROQ_API_KEY_1 Missing → AI Disabled")

except Exception as e:
    print(f"⚠️ Failed to Initialize Orchestrator: {e}")
    orchestrator = None


# ------------------------------------------------------------
# ✅ Default Group Setup (ALL AGENTS ENABLED)
# ------------------------------------------------------------

def initialize_default_groups():
    if not groups_db:
        groups_db["group_general"] = {
            "id": "group_general",
            "name": "General Chat",
            "avatar": "💬",
            "members": [],
            "agents": [
                "agent_research",
                "agent_analysis",
                "agent_synthesis",
            ],
            "created_at": datetime.now().isoformat(),
            "last_message": "Welcome!",
            "last_message_time": datetime.now().isoformat(),
        }


initialize_default_groups()


# ------------------------------------------------------------
# ✅ Root Endpoint
# ------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "WhatsApp-like Chat API is running"}


# ------------------------------------------------------------
# ✅ Groups API
# ------------------------------------------------------------

@app.get("/api/groups")
def get_groups():
    return {"groups": list(groups_db.values())}


@app.post("/api/groups")
def create_group(request: CreateGroupRequest):
    group_id = f"group_{uuid.uuid4().hex[:8]}"

    new_group = {
        "id": group_id,
        "name": request.name,
        "avatar": request.avatar or "👥",
        "members": request.members or [],
        "agents": request.agents or [],
        "created_at": datetime.now().isoformat(),
        "last_message": "",
        "last_message_time": datetime.now().isoformat(),
    }

    groups_db[group_id] = new_group
    return {"success": True, "group": new_group}


@app.get("/api/groups/{group_id}")
def get_group(group_id: str):
    if group_id not in groups_db:
        raise HTTPException(status_code=404, detail="Group not found")
    return groups_db[group_id]


@app.post("/api/groups/{group_id}/members")
def add_member(group_id: str, request: AddMemberRequest):
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
    if group_id not in groups_db:
        raise HTTPException(status_code=404, detail="Group not found")

    group = groups_db[group_id]

    if member_id in group["members"]:
        group["members"].remove(member_id)

    if member_id in group["agents"]:
        group["agents"].remove(member_id)

    return {"success": True, "group": group}


@app.get("/api/agents")
def get_available_agents():
    return {"agents": AVAILABLE_AGENTS}


# ------------------------------------------------------------
# ✅ Query API (Non-WebSocket)
# ------------------------------------------------------------

@app.post("/api/query", response_model=ConsensusOutput)
async def process_query(request: QueryRequest):

    if not orchestrator:
        return ConsensusOutput(
            final_answer="AI agents unavailable.",
            mode_used="none",
            agent_responses=[],
        )

    result = orchestrator.execute_query(request.message)

    return ConsensusOutput(
        final_answer=result["final_answer"],
        mode_used=result["mode_used"],
        agent_responses=result["agent_responses"],
    )


# ------------------------------------------------------------
# ✅ Robust Agent Resolver (Fixes Missing Agent 3)
# ------------------------------------------------------------

def resolve_agent_id(agent_name: str) -> str | None:

    name = agent_name.lower()

    if "agent 1" in name or "lead" in name or "generator" in name:
        return "agent_research"

    if "agent 2" in name or "critic" in name or "supplement" in name:
        return "agent_analysis"

    if "agent 3" in name or "supporter" in name or "synthesis" in name:
        return "agent_synthesis"

    return None


# ------------------------------------------------------------
# ✅ WebSocket Chat Endpoint
# ------------------------------------------------------------

@app.websocket("/ws/{room_id}/{user_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_name: str):

    await manager.connect(websocket, room_id, user_name)

    await manager.broadcast_to_room(
        {
            "type": "user_joined",
            "user_name": user_name,
            "online_users": manager.get_room_users(room_id),
            "timestamp": datetime.now().isoformat(),
        },
        room_id,
    )

    try:
        while True:

            # Receive user message
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("message", "").strip()
            if not user_message:
                continue

            # Broadcast user message instantly
            await manager.broadcast_to_room(
                {
                    "type": "user_message",
                    "user_name": user_name,
                    "content": user_message,
                    "timestamp": datetime.now().isoformat(),
                },
                room_id,
            )

            # Skip AI if orchestrator disabled
            if not orchestrator or room_id not in groups_db:
                continue

            group = groups_db[room_id]

            if not group["agents"]:
                continue

            print(f"\n🤖 Agents Active: {group['agents']}")

            # Run AI Pipeline
            result = orchestrator.execute_query(user_message)

            mode_used = result["mode_used"]
            agent_responses = result["agent_responses"]
            final_answer = result["final_answer"]

            # Mode Info
            await manager.broadcast_to_room(
                {
                    "type": "system",
                    "content": f"⚙️ Mode Selected: {mode_used.upper()}",
                    "timestamp": datetime.now().isoformat(),
                },
                room_id,
            )

            # Sort responses for consistent order
            agent_responses.sort(key=lambda r: r["agent_name"])

            # Stream each agent response
            for response in agent_responses:

                agent_name = response.get("agent_name", "Unknown")
                content = response.get("content", "").strip()

                if not content:
                    continue

                agent_id = resolve_agent_id(agent_name)

                if not agent_id:
                    continue

                if agent_id not in group["agents"]:
                    continue

                await manager.broadcast_to_room(
                    {
                        "type": "agent_response",
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "content": content,
                        "mode_used": mode_used,
                        "timestamp": datetime.now().isoformat(),
                    },
                    room_id,
                )

            # Final Consensus
            await manager.broadcast_to_room(
                {
                    "type": "consensus",
                    "content": final_answer.strip(),
                    "mode_used": mode_used,
                    "timestamp": datetime.now().isoformat(),
                },
                room_id,
            )

    except WebSocketDisconnect:

        manager.disconnect(websocket, room_id)

        await manager.broadcast_to_room(
            {
                "type": "user_left",
                "user_name": user_name,
                "online_users": manager.get_room_users(room_id),
                "timestamp": datetime.now().isoformat(),
            },
            room_id,
        )


# ------------------------------------------------------------
# ✅ Run Server
# ------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
