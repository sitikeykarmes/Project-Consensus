from sqlalchemy.orm import Session
from app.db.models import Message


# -------------------------
# Save Message
# -------------------------
def save_message(
    db: Session,
    group_id: str,
    sender_id: str,
    sender_name: str,
    sender_type: str,
    content: str,
):
    msg = Message(
        group_id=group_id,
        sender_id=sender_id,
        sender_name=sender_name,
        sender_type=sender_type,
        content=content,
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)

    return msg


# -------------------------
# Load Recent Messages
# -------------------------
def load_recent_messages(
    db: Session,
    group_id: str,
    limit: int = 20
):
    return (
        db.query(Message)
        .filter(Message.group_id == group_id)
        .order_by(Message.timestamp.asc())
        .limit(limit)
        .all()
    )
