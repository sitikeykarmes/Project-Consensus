# backend/app/agents/opposition_mode.py

from app.utils.LLM_agent_client import LLMAgentClient


CHAT_RULES = """
You are inside a WhatsApp group chat with other AI agents.

Rules:
- Replies must be SHORT.
- No essays, no markdown tables.
- Write essays, detailed explanation, full working code, give long tables, bullet lists, etc. only when the user explicitly asks for it.
- Only key point.
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
                + "\nRole: Agent 1 (Generator). Give an initial short but valuable answer with most important details."
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
                + "\nRole: Agent 2 (Critic). Attack the Generator's logic and highlight flaws or omissions in their answer briefly."
            },
            {
                "role": "user",
                "content": f"""{context_block}
User Query: {user_query}

Defendant said:
{generator_text}

Reply with short attack or disagreement.
""",
            },
        ]
        return self.client.get_completion("agent2", messages, temperature=0.4, max_tokens=90)

    def investigator_agent(self, user_query: str, gen: str, critic: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\nPrevious conversation context:\n{context}\n"
        messages = [
            {
                "role": "system",
                "content": CHAT_RULES
                + """
Role: Agent 3 (Investigator / Fact-Checker).
Your job:
- Strict fact-checking of dates, names, logic, and claims.
- Read Generator and Critic.
- Output a concrete Fact-Check Report.
- Do NOT issue a final verdict.
"""
            },
            {
                "role": "user",
                "content": f"""{context_block}
User Query: {user_query}

Generator:
{gen}

Critic:
{critic}

Give a strictly factual investigation report.
""",
            },
        ]
        return self.client.get_completion("agent3", messages, temperature=0.3, max_tokens=110)

    def judge_agent(self, user_query: str, gen: str, critic: str, investigation: str, round_no: int, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\nPrevious conversation context:\n{context}\n"
            
        round_instruction = ""
        if round_no < 3:
            round_instruction = f"This is only Round {round_no}. DO NOT declare 'VERDICT REACHED' yet. Instead, issue an interim judgment and instruct the Generator/Critic on what needs more debate."
        else:
            round_instruction = f"This is Round {round_no} (max 5). If the debate is settled, you MUST say: VERDICT REACHED. Otherwise, keep debating."
            
        messages = [
            {
                "role": "system",
                "content": CHAT_RULES
                + f"""
Role: Agent 4 (Chief Judge).
Your job:
- Read Generator, Critic, and Investigator.
- Decide who is accurate.
- Issue a binding VERDICT for the Generator to follow.
{round_instruction}
"""
            },
            {
                "role": "user",
                "content": f"""{context_block}
User Query: {user_query}

Generator:
{gen}

Critic:
{critic}

Investigator Fact-Check:
{investigation}

Give your judge verdict for this round.
""",
            },
        ]
        return self.client.get_completion("agent4", messages, temperature=0.3, max_tokens=120)

    def generator_update(self, user_query: str, judge_verdict: str, context: str = "") -> str:
        context_block = ""
        if context:
            context_block = f"\nPrevious conversation context:\n{context}\n"
        messages = [
            {
                "role": "system",
                "content": CHAT_RULES
                + "\nRole: Agent 1 (Generator). Update your answer strictly based on the Chief Judge's verdict."
            },
            {
                "role": "user",
                "content": f"""{context_block}
User Query: {user_query}

Chief Judge Verdict:
{judge_verdict}

Now rewrite your answer.
""",
            },
        ]
        return self.client.get_completion("agent1", messages, temperature=0.6, max_tokens=100)

    def run(self, user_query: str, context: str = "") -> dict:
        print("Running Opposition Mode Debate (Courtroom Model)...")
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

            investigation_text = self.investigator_agent(user_query, generator_text, critic_text, context)
            responses.append({
                "agent_name": f"Investigator (Agent 3) Round {round_no}",
                "content": investigation_text,
                "mode": "opposition"
            })

            judge_text = self.judge_agent(user_query, generator_text, critic_text, investigation_text, round_no, context)
            responses.append({
                "agent_name": f"Chief Judge (Agent 4) Round {round_no}",
                "content": judge_text,
                "mode": "opposition"
            })

            if round_no >= 3 and "verdict reached" in judge_text.lower():
                break

            generator_text = self.generator_update(user_query, judge_text, context)
            responses.append({
                "agent_name": f"Generator Update Round {round_no}",
                "content": generator_text,
                "mode": "opposition"
            })

        return {
            "mode": "opposition",
            "responses": responses
        }
