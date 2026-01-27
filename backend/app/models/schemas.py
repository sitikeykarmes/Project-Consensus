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
