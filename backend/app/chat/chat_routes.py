from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Message, GroupMember
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


# ✅ Send Message
@router.post("/send/{group_id}")
def send_message(
    group_id: str,
    content: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    # Ensure user is member
    member = db.query(GroupMember).filter_by(
        group_id=group_id,
        user_id=user.id
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a group member")

    msg = Message(
        group_id=group_id,
        sender_id=user.id,
        sender_name=user.email,
        sender_type="user",
        content=content
    )

    db.add(msg)
    db.commit()

    return {"message": "Message sent"}


# ✅ Get Chat History (Memory)
@router.get("/history/{group_id}")
def chat_history(
    group_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    messages = db.query(Message).filter_by(group_id=group_id).order_by(Message.timestamp).all()

    return [
        {
            "sender": m.sender_id,
            "content": m.content,
            "time": m.timestamp
        }
        for m in messages
    ]
