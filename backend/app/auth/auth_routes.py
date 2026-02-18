from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.db.models import User
from app.auth.auth_utils import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.db.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# -------------------------
# SIGNUP
# -------------------------
@router.post("/signup")
def signup(email: str, password: str, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"success": True, "message": "User created successfully"}


# -------------------------
# LOGIN
# -------------------------
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # ✅ Put user_id inside token
    token = create_access_token({
        "user_id": user.id,
        "email": user.email
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }
