# backend/app/agents/support_mode.py

from app.utils.LLM_agent_client import LLMAgentClient


CHAT_RULES = """
You are inside a WhatsApp group chat with other AI agents.

Rules:
- Replies must be short (max 2-3 lines until asked for long answer).
- Do NOT write long essays or tables until asked.
- Write essays, give long tables, bullet lists, etc. only when the user explicitly asks for it.
- Do NOT repeat what others said.
- Add only 1-3 useful new points.
- If conversation context is provided, use it to give more relevant answers.
"""


class SupportMode:
    def __init__(self):
        self.client = LLMAgentClient()

    def lead_agent(self, user_query: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\n\nPrevious conversation context:\n{context}\n\nNow answer:"
        messages = [
            {"role": "system",
             "content": CHAT_RULES + "\nRole: Agent 1. Give the main answer briefly."},
            {"role": "user", "content": f"{context_block}\n{user_query}"},
        ]
        return self.client.get_completion("agent1", messages, temperature=0.6, max_tokens=120)

    def supplementer_agent(self, user_query: str, lead_response: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\nPrevious conversation context:\n{context}\n"
        messages = [
            {"role": "system",
             "content": CHAT_RULES + "\nRole: Agent 2. Add extra helpful nuance."},
            {"role": "user",
             "content": f"""{context_block}
User query: {user_query}

Agent 1 said:
{lead_response}

Add 1-2 extra points (no repetition).
"""}
        ]
        return self.client.get_completion("agent2", messages, temperature=0.7, max_tokens=100)

    def third_agent(self, user_query: str, previous: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\nPrevious conversation context:\n{context}\n"
        messages = [
            {"role": "system",
             "content": CHAT_RULES +
                        "\nRole: Agent 3. Give a final practical takeaway or caution."},
            {"role": "user",
             "content": f"""{context_block}
User query: {user_query}

So far agents said:
{previous}

Add final useful takeaway (short).
"""}
        ]
        return self.client.get_completion("agent3", messages, temperature=0.7, max_tokens=80)

    def run(self, user_query: str, context: str = "") -> dict:
        print("Running Support Mode...")
        lead = self.lead_agent(user_query, context)
        supplement = self.supplementer_agent(user_query, lead, context)
        third = self.third_agent(user_query, lead + "\n" + supplement, context)

        return {
            "mode": "support",
            "responses": [
                {"agent_name": "Agent 1", "content": lead, "mode": "support"},
                {"agent_name": "Agent 2", "content": supplement, "mode": "support"},
                {"agent_name": "Agent 3", "content": third, "mode": "support"},
            ],
        }
