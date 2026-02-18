# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from app.db.init_db import init_database
from app.db.database import SessionLocal

from app.db.message_service import save_message, load_recent_messages

from app.auth.auth_routes import router as auth_router
from app.groups.group_routes import router as group_router
from app.chat.chat_routes import router as chat_router
from app.auth.ws_auth import get_user_from_token
from app.models.schemas import (
    Group,
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


env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="WhatsApp-like Chat API")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
init_database()
active_connections = {}
app.include_router(auth_router)
app.include_router(group_router)
app.include_router(chat_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


groups_db: Dict[str, dict] = {}

AVAILABLE_AGENTS = [
    {"id": "agent_research", "name": "Agent 1", "type": "agent", "avatar": "A1"},
    {"id": "agent_analysis", "name": "Agent 2", "type": "agent", "avatar": "A2"},
    {"id": "agent_synthesis", "name": "Agent 3", "type": "agent", "avatar": "A3"},
]


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

orchestrator = None

try:
    groq_key_1 = os.getenv("GROQ_API_KEY_1")
    if groq_key_1:
        print("GROQ API Key Loaded")
        orchestrator = Orchestrator()
        print("Orchestrator Initialized Successfully")
    else:
        print("GROQ_API_KEY_1 Missing - AI Disabled")
except Exception as e:
    print(f"Failed to Initialize Orchestrator: {e}")
    orchestrator = None


def initialize_default_groups():
    if not groups_db:
        groups_db["group_general"] = {
            "id": "group_general",
            "name": "General Chat",
            "avatar": "GC",
            "members": [],
            "agents": ["agent_research", "agent_analysis", "agent_synthesis"],
            "created_at": datetime.now().isoformat(),
            "last_message": "Welcome!",
            "last_message_time": datetime.now().isoformat(),
        }

initialize_default_groups()


@app.get("/")
def read_root():
    return {"message": "WhatsApp-like Chat API is running"}


@app.get("/api/agents")
def get_available_agents():
    return {"agents": AVAILABLE_AGENTS}


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


def resolve_agent_id(agent_name: str) -> str | None:
    name = agent_name.lower()
    if "agent 1" in name or "lead" in name or "generator" in name:
        return "agent_research"
    if "agent 2" in name or "critic" in name:
        return "agent_analysis"
    if "agent 3" in name or "referee" in name or "synthesis" in name:
        return "agent_synthesis"
    return None


def build_conversation_history(room_id: str, limit: int = 10) -> list:
    """Load recent messages from DB and format as conversation history for AI context."""
    db = SessionLocal()
    try:
        messages = (
            db.query(__import__('app.db.models', fromlist=['Message']).Message)
            .filter(__import__('app.db.models', fromlist=['Message']).Message.group_id == room_id)
            .order_by(__import__('app.db.models', fromlist=['Message']).Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        messages.reverse()  # oldest first
        
        history = []
        for msg in messages:
            if msg.sender_type == "user":
                history.append({
                    "role": "user",
                    "name": msg.sender_name,
                    "content": msg.content
                })
            elif msg.sender_type == "consensus":
                history.append({
                    "role": "assistant",
                    "name": "AI Consensus",
                    "content": msg.content
                })
        return history
    finally:
        db.close()


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    user = get_user_from_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    user_email = user.email
    await manager.connect(websocket, room_id, user_email)

    # Load previous messages when user joins
    db = SessionLocal()
    try:
        recent_messages = load_recent_messages(db, room_id, limit=50)
        for msg in recent_messages:
            msg_data = {
                "type": msg.sender_type,
                "sender_id": msg.sender_id,
                "sender_name": msg.sender_name,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            # If it's a consensus message, try to parse metadata
            if msg.sender_type == "consensus" and msg.extra_data:
                try:
                    meta = json.loads(msg.extra_data)
                    msg_data["mode_used"] = meta.get("mode_used", "")
                    msg_data["agent_responses"] = meta.get("agent_responses", [])
                except:
                    pass
            await websocket.send_json(msg_data)
    finally:
        db.close()

    # Broadcast join
    await manager.broadcast_to_room(
        {
            "type": "user_joined",
            "user_name": user_email,
            "online_users": manager.get_room_users(room_id),
            "timestamp": datetime.now().isoformat(),
        },
        room_id,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("message", "").strip()
            if not user_message:
                continue

            # Save user message
            db = SessionLocal()
            try:
                save_message(
                    db=db,
                    group_id=room_id,
                    sender_id=user.id,
                    sender_name=user_email,
                    sender_type="user",
                    content=user_message,
                )
            finally:
                db.close()

            # Broadcast user message
            await manager.broadcast_to_room(
                {
                    "type": "user",
                    "sender_id": user.id,
                    "sender_name": user_email,
                    "content": user_message,
                    "timestamp": datetime.now().isoformat(),
                },
                room_id,
            )

            # AI Processing
            if not orchestrator:
                continue

            # Fetch group from DB
            db = SessionLocal()
            try:
                from app.db.models import Group as GroupModel
                group_obj = db.query(GroupModel).filter(GroupModel.id == room_id).first()
            finally:
                db.close()

            if not group_obj:
                continue

            agents = json.loads(group_obj.agents) if group_obj.agents else []
            if not agents:
                continue

            # Send typing indicator
            await manager.broadcast_to_room(
                {
                    "type": "typing",
                    "sender_name": "AI Agents",
                    "timestamp": datetime.now().isoformat(),
                },
                room_id,
            )

            # Build conversation history for context
            conversation_history = build_conversation_history(room_id, limit=10)

            # Execute orchestrator with context
            result = orchestrator.execute_query(user_message, conversation_history)

            agent_responses = result["agent_responses"]
            final_answer = result["final_answer"]
            mode_used = result["mode_used"]

            # Save consensus with metadata (agent responses bundled)
            metadata = json.dumps({
                "mode_used": mode_used,
                "agent_responses": agent_responses
            })

            db = SessionLocal()
            try:
                save_message(
                    db=db,
                    group_id=room_id,
                    sender_id="consensus",
                    sender_name="AI Consensus",
                    sender_type="consensus",
                    content=final_answer.strip(),
                    metadata=metadata,
                )
            finally:
                db.close()

            # Send bundled consensus message (with agent responses inside)
            await manager.broadcast_to_room(
                {
                    "type": "consensus",
                    "sender_name": "AI Consensus",
                    "content": final_answer.strip(),
                    "mode_used": mode_used,
                    "agent_responses": agent_responses,
                    "timestamp": datetime.now().isoformat(),
                },
                room_id,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast_to_room(
            {
                "type": "user_left",
                "user_name": user_email,
                "online_users": manager.get_room_users(room_id),
            },
            room_id,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
