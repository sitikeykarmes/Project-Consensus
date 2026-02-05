from dotenv import load_dotenv

# Load environment variables before importing app
load_dotenv()

from app.main import app

__all__ = ["app"]
