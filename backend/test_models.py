import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY_1", os.getenv("GROQ_API_KEY")))
models = client.models.list()
for m in models.data:
    print(m.id)
