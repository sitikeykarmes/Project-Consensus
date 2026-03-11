# app/db/init_db.py
from app.db.database import engine
from app.db.models import Base, User, Group, GroupMember, Message, ConversationSummary  # ← explicit imports


def init_database():
    print("✅ Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database ready!")