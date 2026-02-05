# backend/app/agents/support_mode.py

from app.utils.LLM_agent_client import LLMAgentClient


CHAT_RULES = """
You are inside a WhatsApp group chat with other AI agents.

Rules:
- Replies must be short (max 2-3 lines until asked for longer answer).
- Do NOT write long essays, tables, or bullet lists until asked.
- Write essays, give long tables, bullet lists, etc. only when the user explicitly asks for it.
- Do NOT rewrite the full answer.
- Add 2-3 extra useful points.
- Avoid repetition.
"""


class SupportMode:
    def __init__(self):
        self.client = LLMAgentClient()

    def lead_agent(self, user_query: str) -> str:
        messages = [
            {"role": "system", "content": CHAT_RULES + "\nRole: Lead Agent. Start the answer briefly."},
            {"role": "user", "content": user_query},
        ]

        return self.client.get_completion("agent1", messages, temperature=0.6, max_tokens=200)

    def supplementer_agent(self, user_query: str, lead_response: str) -> str:
        messages = [
            {"role": "system", "content": CHAT_RULES + "\nRole: Support Agent. Add 1-3 extra points."},
            {
                "role": "user",
                "content": f"""
User query: {user_query}

Agent 1 said:
{lead_response}

Add extra helpful point/points (do not repeat).
""",
            },
        ]

        return self.client.get_completion("agent2", messages, temperature=0.7, max_tokens=80)

    def third_agent(self, user_query: str, previous: str) -> str:
        messages = [
            {"role": "system", "content": CHAT_RULES + "\nRole: Support Agent 3. Add final small nuance."},
            {
                "role": "user",
                "content": f"""
User query: {user_query}

Previous agents said:
{previous}

Add more helpful point, very short.
""",
            },
        ]

        return self.client.get_completion("agent3", messages, temperature=0.7, max_tokens=80)

    def run(self, user_query: str) -> dict:
        print("🤖 Running Support Mode...")

        lead = self.lead_agent(user_query)
        supplement = self.supplementer_agent(user_query, lead)
        third = self.third_agent(user_query, lead + "\n" + supplement)

        return {
            "mode": "support",
            "responses": [
                {"agent_name": "Lead Agent (Agent 1)", "content": lead, "mode": "support"},
                {"agent_name": "Supplementer (Agent 2)", "content": supplement, "mode": "support"},
                {"agent_name": "Supporter (Agent 3)", "content": third, "mode": "support"},
            ],
        }
