# backend/app/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class QueryRequest(BaseModel):
    room_id: str
    user_name: str
    message: str

class AgentResponse(BaseModel):
    agent_name: str
    content: str
    mode: str

class ConsensusOutput(BaseModel):
    final_answer: str
    mode_used: str
    agent_responses: List[AgentResponse]

class Group(BaseModel):
    id: str
    name: str
    avatar: Optional[str] = None
    members: List[str]
    agents: List[str]
    created_at: str
    last_message: Optional[str] = ""
    last_message_time: Optional[str] = ""

class CreateGroupRequest(BaseModel):
    name: str
    avatar: Optional[str] = None
    members: Optional[List[str]] = []
    agents: Optional[List[str]] = []

class AddMemberRequest(BaseModel):
    member_id: str
    member_type: str  # "user" or "agent"