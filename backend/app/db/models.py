from sqlalchemy import Column, Integer,String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base


def generate_id():
    return str(uuid.uuid4())


# -------------------------
# USER TABLE
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_id)

    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: user memberships
    memberships = relationship(
        "GroupMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# -------------------------
# GROUP TABLE
# -------------------------
class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True)
    name = Column(String)

    # ✅ NEW: Store selected agents as JSON string
    agents = Column(Text, default="[]")

    created_by = Column(Integer)
    created_at = Column(DateTime)

    # Relationships
    members = relationship(
        "GroupMember",
        back_populates="group",
        cascade="all, delete-orphan"
    )

    messages = relationship(
        "Message",
        back_populates="group",
        cascade="all, delete-orphan"
    )


# -------------------------
# GROUP MEMBERS TABLE
# -------------------------
class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(String, primary_key=True, default=generate_id)

    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="memberships")


# -------------------------
# MESSAGE TABLE (User + Agent + System Safe)
# -------------------------
class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_id)

    group_id = Column(String, ForeignKey("groups.id"), nullable=False)

    # Sender info (not FK because agents are not users)
    sender_id = Column(String, nullable=True)

    sender_name = Column(String, nullable=False)
    sender_type = Column(String, default="user")  # user / agent / system

    content = Column(Text, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON string for agent_responses, mode etc.

    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    group = relationship("Group", back_populates="messages")
