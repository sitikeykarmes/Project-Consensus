from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.db.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE group_members ADD COLUMN last_read_at TIMESTAMP"))
        conn.commit()
        print("Successfully added last_read_at to group_members")
except Exception as e:
    if 'already exists' in str(e).lower() or 'duplicate column name' in str(e).lower():
        print("Column already exists, ignoring.")
    else:
        print("Error:", e)
