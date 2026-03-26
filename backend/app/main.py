# backend/app/main.py
import asyncio
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from app.db.init_db import init_database
from app.db.database import SessionLocal

from app.db.message_service import save_message, load_recent_messages
from app.utils.context_builder import build_hybrid_context

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


async def keep_alive():
    await asyncio.sleep(60)  # wait 1 min after startup
    while True:
        try:
            url = os.getenv("RENDER_EXTERNAL_URL", "")
            if url:
                async with httpx.AsyncClient() as client:
                    await client.get(f"{url}/")
                    print("🏓 Keep-alive ping sent.")
        except Exception as e:
            print(f"⚠️ Keep-alive failed: {e}")
        await asyncio.sleep(600)  # ping every 10 minutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(keep_alive())
    yield
    
    
app = FastAPI(title="Consensus", lifespan=lifespan)


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
init_database()
active_connections = {}



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://project-consensus-tau.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(group_router)
app.include_router(chat_router)

groups_db: Dict[str, dict] = {}

AVAILABLE_AGENTS = [
    {"id": "agent_research",  "name": "Agent 1", "type": "agent", "avatar": "A1"},
    {"id": "agent_analysis",  "name": "Agent 2", "type": "agent", "avatar": "A2"},
    {"id": "agent_synthesis", "name": "Agent 3", "type": "agent", "avatar": "A3"},
    {"id": "agent_debate",    "name": "Agent 4 (Debate Mode)", "type": "agent", "avatar": "A4"},
    {"id": "agent_orchestrator", "name": "Agent 5 (Synthesis)", "type": "agent", "avatar": "A5"},
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
            "id":                "group_general",
            "name":              "General Chat",
            "avatar":            "GC",
            "members":           [],
            "agents":            ["agent_research", "agent_analysis", "agent_synthesis", "agent_debate"],
            "created_at":        datetime.now().isoformat(),
            "last_message":      "Welcome!",
            "last_message_time": datetime.now().isoformat(),
        }

initialize_default_groups()


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Consensus Chat API is running"}


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


# ─────────────────────────────────────────────
# WebSocket
# ─────────────────────────────────────────────

@app.websocket("/api/ws/{room_id}")
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

    # ── Load previous messages on join ──
    db = SessionLocal()
    try:
        recent_messages = load_recent_messages(db, room_id, limit=50)
        for msg in recent_messages:
            msg_data = {
                "type":        msg.sender_type,
                "sender_id":   msg.sender_id,
                "sender_name": msg.sender_name,
                "content":     msg.content,
                "timestamp":   msg.timestamp.isoformat(),
            }
            if msg.sender_type == "consensus" and msg.extra_data:
                try:
                    meta = json.loads(msg.extra_data)
                    msg_data["mode_used"]       = meta.get("mode_used", "")
                    msg_data["agent_responses"] = meta.get("agent_responses", [])
                except:
                    pass
            try:
                await websocket.send_json(msg_data)
            except Exception:
                return
    finally:
        db.close()

    # ── Broadcast join ──
    await manager.broadcast_to_room(
        {
            "type":         "user_joined",
            "user_name":    user_email,
            "online_users": manager.get_room_users(room_id),
            "timestamp":    datetime.now().isoformat(),
        },
        room_id,
    )

    try:
        while True:
            data         = await websocket.receive_text()
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
                    "type":        "user",
                    "sender_id":   user.id,
                    "sender_name": user_email,
                    "content":     user_message,
                    "timestamp":   datetime.now().isoformat(),
                },
                room_id,
            )

            if not orchestrator:
                continue

            # Fetch group
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

            # Typing indicator
            await manager.broadcast_to_room(
                {
                    "type":        "typing",
                    "sender_name": "AI Agents",
                    "timestamp":   datetime.now().isoformat(),
                },
                room_id,
            )

            # ── Build hybrid context (summary + recent 15 verbatim) ──
            db = SessionLocal()
            try:
                hybrid_ctx = build_hybrid_context(db, room_id)
            finally:
                db.close()

            conversation_history = hybrid_ctx["conversation_history"]

            # Execute orchestrator with hybrid context
            result = orchestrator.execute_query(
                user_message,
                conversation_history=conversation_history,
            )

            agent_responses = result["agent_responses"]
            final_answer    = result["final_answer"]
            mode_used       = result["mode_used"]

            # Save consensus
            metadata = json.dumps({"mode_used": mode_used, "agent_responses": agent_responses})
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

            # Broadcast consensus
            await manager.broadcast_to_room(
                {
                    "type":            "consensus",
                    "sender_name":     "AI Consensus",
                    "content":         final_answer.strip(),
                    "mode_used":       mode_used,
                    "agent_responses": agent_responses,
                    "timestamp":       datetime.now().isoformat(),
                },
                room_id,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast_to_room(
            {
                "type":         "user_left",
                "user_name":    user_email,
                "online_users": manager.get_room_users(room_id),
            },
            room_id,
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)