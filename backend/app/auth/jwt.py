#backend/app/auth/jwt.py
from datetime import datetime, timedelta
from jose import jwt
import os
from dotenv import load_dotenv
from pathlib import Path

# --------------------------------------------------
# Load ENV Variables
# --------------------------------------------------

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Secret key (must exist in .env)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")

# Algorithm
ALGORITHM = "HS256"

# Token expiry time
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# --------------------------------------------------
# ✅ Create JWT Token
# --------------------------------------------------

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt
