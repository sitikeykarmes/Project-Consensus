# backend/app/agents/opposition_mode.py

from app.utils.LLM_agent_client import LLMAgentClient


CHAT_RULES = """
You are inside a WhatsApp group chat with other AI agents.

Rules:
- Replies must be SHORT (max 2-3 lines until asked for longer answer).
- No essays, no markdown tables.
- Write essays, give long tables, bullet lists, etc. only when the user explicitly asks for it.
- Only key point per message.
- Speak naturally like ChatGPT/Gemini in a group.
- If conversation context is provided, use it to give more relevant answers.
"""


class OppositionMode:
    def __init__(self):
        self.client = LLMAgentClient()

    def generator_agent(self, user_query: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\n\nPrevious conversation context:\n{context}\n\nNow answer:"
        messages = [
            {
                "role": "system",
                "content": CHAT_RULES
                + "\nRole: Agent 1 (Generator). Give an initial short answer."
            },
            {"role": "user", "content": f"{context_block}\n{user_query}"},
        ]
        return self.client.get_completion("agent1", messages, temperature=0.7, max_tokens=120)

    def critic_agent(self, user_query: str, generator_text: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\nPrevious conversation context:\n{context}\n"
        messages = [
            {
                "role": "system",
                "content": CHAT_RULES
                + "\nRole: Agent 2 (Critic). Challenge or correct Agent 1 briefly."
            },
            {
                "role": "user",
                "content": f"""{context_block}
User Query: {user_query}

Agent 1 said:
{generator_text}

Reply with short correction or disagreement.
""",
            },
        ]
        return self.client.get_completion("agent2", messages, temperature=0.4, max_tokens=90)

    def referee_agent(self, user_query: str, gen: str, critic: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\nPrevious conversation context:\n{context}\n"
        messages = [
            {
                "role": "system",
                "content": CHAT_RULES
                + """
Role: Agent 3 (Referee).
Your job:
- Decide who is more accurate
- Remove hallucinations
- Give a short verified verdict
If debate is settled, say: VERDICT REACHED
"""
            },
            {
                "role": "user",
                "content": f"""{context_block}
User Query: {user_query}

Agent 1 answer:
{gen}

Agent 2 critique:
{critic}

Give a short referee verdict.
""",
            },
        ]
        return self.client.get_completion("agent3", messages, temperature=0.3, max_tokens=110)

    def generator_update(self, user_query: str, referee_note: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\nPrevious conversation context:\n{context}\n"
        messages = [
            {
                "role": "system",
                "content": CHAT_RULES
                + "\nRole: Agent 1. Update your answer based on the referee."
            },
            {
                "role": "user",
                "content": f"""{context_block}
User Query: {user_query}

Referee feedback:
{referee_note}

Now rewrite your answer in 2-3 lines.
""",
            },
        ]
        return self.client.get_completion("agent1", messages, temperature=0.6, max_tokens=100)

    def run(self, user_query: str, context: str = "") -> dict:
        print("Running Opposition Mode Debate (3-Agent)...")
        responses = []

        generator_text = self.generator_agent(user_query, context)
        responses.append({
            "agent_name": "Generator (Agent 1)",
            "content": generator_text,
            "mode": "opposition"
        })

        for round_no in range(1, 6):
            critic_text = self.critic_agent(user_query, generator_text, context)
            responses.append({
                "agent_name": f"Critic (Agent 2) Round {round_no}",
                "content": critic_text,
                "mode": "opposition"
            })

            referee_text = self.referee_agent(user_query, generator_text, critic_text, context)
            responses.append({
                "agent_name": f"Referee (Agent 3) Round {round_no}",
                "content": referee_text,
                "mode": "opposition"
            })

            if "verdict reached" in referee_text.lower():
                break

            generator_text = self.generator_update(user_query, referee_text, context)
            responses.append({
                "agent_name": f"Generator Update Round {round_no}",
                "content": generator_text,
                "mode": "opposition"
            })

        return {
            "mode": "opposition",
            "responses": responses
        }
