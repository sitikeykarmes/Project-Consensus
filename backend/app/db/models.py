from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
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
    agents = Column(Text, default="[]")
    created_by = Column(Integer)
    created_at = Column(DateTime)

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
    # ← NEW: one summary row per group
    summary = relationship(
        "ConversationSummary",
        back_populates="group",
        cascade="all, delete-orphan",
        uselist=False  # one-to-one
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

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="memberships")


# -------------------------
# MESSAGE TABLE
# -------------------------
class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_id)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    sender_id = Column(String, nullable=True)
    sender_name = Column(String, nullable=False)
    sender_type = Column(String, default="user")  # user / agent / system / consensus
    content = Column(Text, nullable=False)
    extra_data = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="messages")


# -------------------------
# CONVERSATION SUMMARY TABLE  ← NEW
# -------------------------
class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"

    id               = Column(String, primary_key=True, default=generate_id)
    group_id         = Column(String, ForeignKey("groups.id"), nullable=False, unique=True, index=True)
    summary_text     = Column(Text, nullable=False)       # compressed older context
    messages_covered = Column(Integer, default=0)         # how many messages are summarized
    last_message_id  = Column(String, nullable=True)      # id of last message included
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("Group", back_populates="summary")