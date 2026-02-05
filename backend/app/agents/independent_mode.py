# backend/app/agents/independent_mode.py

from app.utils.LLM_agent_client import LLMAgentClient


CHAT_RULES = """
You are an AI agent inside a WhatsApp-style group chat.

Other AI agents are also responding to the same user query.

Rules:
- Keep your reply short (max 3-4 lines until asked for longer answer).
- Do NOT write long essays, tables, or bullet lists until asked.
- Write essays, give long tables, bullet lists, etc. only when the user explicitly asks for it.
- Give only your unique perspective.
- Sound like ChatGPT/Gemini in chat.
"""


class IndependentMode:
    def __init__(self):
        self.client = LLMAgentClient()

    def agent_1(self, user_query: str) -> dict:
        messages = [
            {"role": "system", "content": CHAT_RULES + "\nRole: Agent 1. Give the first helpful answer."},
            {"role": "user", "content": user_query},
        ]

        content = self.client.get_completion(
            "agent1", messages, temperature=0.6, max_tokens=200
        )

        return {"agent_name": "Agent 1 (Agent 1)", "content": content, "mode": "independent"}

    def agent_2(self, user_query: str) -> dict:
        messages = [
            {"role": "system", "content": CHAT_RULES + "\nRole: Agent 2. Give a different angle or nuance."},
            {"role": "user", "content": user_query},
        ]

        content = self.client.get_completion(
            "agent2", messages, temperature=0.7, max_tokens=120
        )

        return {"agent_name": "Agent 2 (Agent 2)", "content": content, "mode": "independent"}

    def agent_3(self, user_query: str) -> dict:
        messages = [
            {"role": "system", "content": CHAT_RULES + "\nRole: Agent 3. Add a perspective others may miss."},
            {"role": "user", "content": user_query},
        ]

        content = self.client.get_completion(
            "agent3", messages, temperature=0.7, max_tokens=120
        )

        return {"agent_name": "Agent 3 (Agent 3)", "content": content, "mode": "independent"}

    def run(self, user_query: str) -> dict:
        print("🤖 Running Independent Mode...")

        results = [
            self.agent_1(user_query),
            self.agent_2(user_query),
            self.agent_3(user_query),
        ]

        return {"mode": "independent", "responses": results}
