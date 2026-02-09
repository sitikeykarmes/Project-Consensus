from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime
import json
from app.db.database import get_db
from app.db.models import Group, GroupMember
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/groups", tags=["Groups"])



# ✅ Request Body Schema
class CreateGroupBody(BaseModel):
    name: str
    agents: List[str] = []


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

    return {
        "success": True,
        "group": {
            "id": group.id,
            "name": group.name,
            "agents": body.agents,   # frontend remembers
            "avatar": "👥",
        },
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