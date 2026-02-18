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
- If conversation context is provided, use it to give more relevant answers.
"""


class IndependentMode:
    def __init__(self):
        self.client = LLMAgentClient()

    def _build_messages(self, system_suffix: str, user_query: str, context: str = ""):
        context_block = ""
        if context:
            context_block = f"\n\nPrevious conversation context:\n{context}\n\nNow answer this new query:"
        
        return [
            {"role": "system", "content": CHAT_RULES + system_suffix},
            {"role": "user", "content": f"{context_block}\n{user_query}"},
        ]

    def agent_1(self, user_query: str, context: str = "") -> dict:
        messages = self._build_messages(
            "\nRole: Agent 1. Give the first helpful answer.",
            user_query, context
        )
        content = self.client.get_completion("agent1", messages, temperature=0.6, max_tokens=200)
        return {"agent_name": "Agent 1", "content": content, "mode": "independent"}

    def agent_2(self, user_query: str, context: str = "") -> dict:
        messages = self._build_messages(
            "\nRole: Agent 2. Give a different angle or nuance.",
            user_query, context
        )
        content = self.client.get_completion("agent2", messages, temperature=0.7, max_tokens=120)
        return {"agent_name": "Agent 2", "content": content, "mode": "independent"}

    def agent_3(self, user_query: str, context: str = "") -> dict:
        messages = self._build_messages(
            "\nRole: Agent 3. Add a perspective others may miss.",
            user_query, context
        )
        content = self.client.get_completion("agent3", messages, temperature=0.7, max_tokens=120)
        return {"agent_name": "Agent 3", "content": content, "mode": "independent"}

    def run(self, user_query: str, context: str = "") -> dict:
        print("Running Independent Mode...")
        results = [
            self.agent_1(user_query, context),
            self.agent_2(user_query, context),
            self.agent_3(user_query, context),
        ]
        return {"mode": "independent", "responses": results}
