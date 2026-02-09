from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import json
from app.db.database import get_db
from app.db.models import Group, GroupMember, User
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/groups", tags=["Groups"])



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
    # Check duplicate name
    existing = db.query(Group).filter(Group.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group name already exists")

    # Create group
    group = Group(
        id=str(uuid.uuid4()),
        name=body.name,
        # ✅ Save agents into DB
        agents=json.dumps(body.agents),
        created_by=user.id,
        created_at=datetime.utcnow(),
    )

    db.add(group)
    db.commit()
    db.refresh(group)

    # ✅ Creator auto joins
    member = GroupMember(group_id=group.id, user_id=user.id)
    db.add(member)
    db.commit()

    # ✅ Add invited members by email
    added_members = []
    failed_members = []

    if body.member_emails:
        for email in body.member_emails:
            email = email.strip().lower()
            
            # Skip if it's the creator's email
            if email == user.email.lower():
                continue
            
            # Find user by email
            invited_user = db.query(User).filter(User.email == email).first()
            
            if not invited_user:
                failed_members.append({"email": email, "reason": "User not found"})
                continue
            
            # Check if already a member
            existing_member = db.query(GroupMember).filter_by(
                group_id=group.id,
                user_id=invited_user.id
            ).first()
            
            if existing_member:
                failed_members.append({"email": email, "reason": "Already a member"})
                continue
            
            # Add member
            new_member = GroupMember(group_id=group.id, user_id=invited_user.id)
            db.add(new_member)
            added_members.append({"email": email, "user_id": invited_user.id})
        
        db.commit()

    return {
        "success": True,
        "group": {
            "id": group.id,
            "name": group.name,
            "agents": body.agents,
            "avatar": "👥",
        },
        "added_members": added_members,
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

    existing = (
        db.query(GroupMember)
        .filter_by(group_id=group_id, user_id=user.id)
        .first()
    )

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
    memberships = (
        db.query(GroupMember)
        .filter(GroupMember.user_id == user.id)
        .all()
    )

    group_ids = [m.group_id for m in memberships]

    groups = db.query(Group).filter(Group.id.in_(group_ids)).all()

    return {
    "groups": [
        {
            "id": g.id,
            "name": g.name,
            "avatar": "💬",

            # ✅ Send agents back to frontend
            "agents": json.loads(g.agents),
        }
        for g in groups
    ]
}


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
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if current user is a member (authorization)
    is_member = db.query(GroupMember).filter_by(
        group_id=group_id,
        user_id=user.id
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    # Add members
    added_members = []
    failed_members = []
    
    for email in body.member_emails:
        email = email.strip().lower()
        
        # Find user by email
        invited_user = db.query(User).filter(User.email == email).first()
        
        if not invited_user:
            failed_members.append({"email": email, "reason": "User not found"})
            continue
        
        # Check if already a member
        existing_member = db.query(GroupMember).filter_by(
            group_id=group_id,
            user_id=invited_user.id
        ).first()
        
        if existing_member:
            failed_members.append({"email": email, "reason": "Already a member"})
            continue
        
        # Add member
        new_member = GroupMember(group_id=group_id, user_id=invited_user.id)
        db.add(new_member)
        added_members.append({"email": email, "user_id": invited_user.id})
    
    db.commit()
    
    return {
        "success": True,
        "added_members": added_members,
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
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if current user is a member
    is_member = db.query(GroupMember).filter_by(
        group_id=group_id,
        user_id=user.id
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    # Get all members
    memberships = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    members = []
    for membership in memberships:
        member_user = db.query(User).filter(User.id == membership.user_id).first()
        if member_user:
            members.append({
                "user_id": member_user.id,
                "email": member_user.email,
                "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
            })
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "members": members,
    }