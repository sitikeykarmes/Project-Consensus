from jose import jwt, JWTError
from fastapi import HTTPException
import os

from app.db.database import SessionLocal
from app.db.models import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("user_id")
        if not user_id:
            return None

        db = SessionLocal()
        user = db.query(User).filter(User.id == user_id).first()
        db.close()

        return user

    except JWTError:
        return None
