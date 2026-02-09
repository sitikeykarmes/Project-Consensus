from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Group, GroupMember
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["Groups"])


# ✅ Create Group
@router.post("/create")
def create_group(
    name: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    new_group = Group(name=name, created_by=user.id)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # Creator automatically joins group
    member = GroupMember(group_id=new_group.id, user_id=user.id)
    db.add(member)
    db.commit()

    return {
        "message": "Group created successfully",
        "group_id": new_group.id
    }


# ✅ Join Group
@router.post("/join/{group_id}")
def join_group(
    group_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    existing = db.query(GroupMember).filter_by(
        group_id=group_id,
        user_id=user.id
    ).first()

    if existing:
        return {"message": "Already a member"}

    member = GroupMember(group_id=group_id, user_id=user.id)
    db.add(member)
    db.commit()

    return {"message": "Joined group successfully"}


# ✅ List My Groups
@router.get("/my")
def my_groups(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    memberships = db.query(GroupMember).filter_by(user_id=user.id).all()

    group_ids = [m.group_id for m in memberships]

    return {
        "user": user.email,
        "groups": group_ids
    }
