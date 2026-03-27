from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import json
from app.db.database import get_db
from app.db.models import Group, GroupMember, User, Message, ConversationSummary
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/api/groups", tags=["Groups"])


# ✅ Request Body Schema
class CreateGroupBody(BaseModel):
    name: str
    agents: List[str] = []
    member_emails: Optional[List[str]] = []


# ✅ Add Members Body Schema
class AddMembersBody(BaseModel):
    member_emails: List[str]


# ---------------------------------------------------
# ✅ Create Group (Stored in DB)
# ---------------------------------------------------
@router.post("/create")
def create_group(
    body: CreateGroupBody,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    existing = db.query(Group).filter(Group.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group name already exists")

    group = Group(
        id=str(uuid.uuid4()),
        name=body.name,
        agents=json.dumps(body.agents),
        created_by=user.id,
        created_at=datetime.utcnow(),
    )

    db.add(group)
    db.commit()
    db.refresh(group)

    member = GroupMember(group_id=group.id, user_id=user.id)
    db.add(member)
    db.commit()

    added_members  = []
    failed_members = []

    if body.member_emails:
        for email in body.member_emails:
            email = email.strip().lower()
            if email == user.email.lower():
                continue
            invited_user = db.query(User).filter(User.email == email).first()
            if not invited_user:
                failed_members.append({"email": email, "reason": "User not found"})
                continue
            existing_member = db.query(GroupMember).filter_by(
                group_id=group.id, user_id=invited_user.id
            ).first()
            if existing_member:
                failed_members.append({"email": email, "reason": "Already a member"})
                continue
            new_member = GroupMember(group_id=group.id, user_id=invited_user.id)
            db.add(new_member)
            added_members.append({"email": email, "user_id": invited_user.id})
        db.commit()

    return {
        "success": True,
        "group": {
            "id":     group.id,
            "name":   group.name,
            "agents": body.agents,
            "avatar": "👥",
        },
        "added_members":  added_members,
        "failed_members": failed_members,
    }


# ---------------------------------------------------
# ✅ Join Group
# ---------------------------------------------------
@router.post("/join/{group_id}")
def join_group(
    group_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = db.query(GroupMember).filter_by(group_id=group_id, user_id=user.id).first()
    if existing:
        return {"message": "Already a member"}

    member = GroupMember(group_id=group_id, user_id=user.id)
    db.add(member)
    db.commit()

    return {"message": "Joined group successfully"}


# ---------------------------------------------------
# ✅ List My Groups (User-Specific)
# ---------------------------------------------------
@router.get("/my")
def my_groups(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == user.id).all()
    group_map = {m.group_id: m for m in memberships}
    group_ids = list(group_map.keys())
    groups = db.query(Group).filter(Group.id.in_(group_ids)).all()

    # Import helper for consistent UTC timestamps
    from app.main import serialize_dt

    results = []
    for g in groups:
        member = group_map[g.id]
        last_msg = db.query(Message).filter(Message.group_id == g.id).order_by(Message.timestamp.desc()).first()
        
        unread_count = 0
        if member.last_read_at and last_msg:
            # Only count messages sent after exactly when the user last read this room
            unread_count = db.query(Message).filter(Message.group_id == g.id, Message.timestamp > member.last_read_at).count()

        results.append({
            "id":     g.id,
            "name":   g.name,
            "avatar": "💬",
            "agents": json.loads(g.agents) if g.agents else [],
            "last_message_content": last_msg.content if last_msg else "No messages yet",
            "last_message_time": serialize_dt(last_msg.timestamp) if last_msg else serialize_dt(g.created_at),
            "unread_count": unread_count
        })

    # Pre-sort on backend for efficiency
    results.sort(key=lambda x: x["last_message_time"], reverse=True)

    return {"groups": results}

# ---------------------------------------------------
# ✅ Mark Group Read (Reset Unread Counter)
# ---------------------------------------------------
@router.post("/{group_id}/read")
def mark_group_read(
    group_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    membership = db.query(GroupMember).filter_by(group_id=group_id, user_id=user.id).first()
    if membership:
        membership.last_read_at = datetime.utcnow()
        db.commit()
    return {"success": True}


# ---------------------------------------------------
# ✅ Add Members to Existing Group
# ---------------------------------------------------
@router.post("/{group_id}/add-members")
def add_members_to_group(
    group_id: str,
    body: AddMembersBody,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    is_member = db.query(GroupMember).filter_by(group_id=group_id, user_id=user.id).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    added_members  = []
    failed_members = []

    for email in body.member_emails:
        email = email.strip().lower()
        invited_user = db.query(User).filter(User.email == email).first()
        if not invited_user:
            failed_members.append({"email": email, "reason": "User not found"})
            continue
        existing_member = db.query(GroupMember).filter_by(
            group_id=group_id, user_id=invited_user.id
        ).first()
        if existing_member:
            failed_members.append({"email": email, "reason": "Already a member"})
            continue
        new_member = GroupMember(group_id=group_id, user_id=invited_user.id)
        db.add(new_member)
        added_members.append({"email": email, "user_id": invited_user.id})

    db.commit()

    return {
        "success":        True,
        "added_members":  added_members,
        "failed_members": failed_members,
    }


# ---------------------------------------------------
# ✅ Get Group Members
# ---------------------------------------------------
@router.get("/{group_id}/members")
def get_group_members(
    group_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    is_member = db.query(GroupMember).filter_by(group_id=group_id, user_id=user.id).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

    memberships = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

    members = []
    for membership in memberships:
        member_user = db.query(User).filter(User.id == membership.user_id).first()
        if member_user:
            members.append({
                "user_id":   member_user.id,
                "email":     member_user.email,
                "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
            })

    return {
        "group_id":   group_id,
        "group_name": group.name,
        "members":    members,
    }


# ---------------------------------------------------
# ✅ Delete Group (creator only)
# ---------------------------------------------------
@router.delete("/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Only the creator can delete
    if str(group.created_by) != str(user.id):
        raise HTTPException(
            status_code=403,
            detail="Only the group creator can delete this group"
        )

    # Delete in FK order to satisfy constraints
    db.query(Message).filter(Message.group_id == group_id).delete()
    db.query(ConversationSummary).filter(ConversationSummary.group_id == group_id).delete()
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    db.query(Group).filter(Group.id == group_id).delete()

    db.commit()

    return {"success": True, "message": f"Group '{group.name}' deleted successfully"}