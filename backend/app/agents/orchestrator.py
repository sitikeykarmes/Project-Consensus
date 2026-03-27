# backend/app/agents/orchestrator.py
from app.agents.opposition_mode import OppositionMode
from app.agents.support_mode import SupportMode
from app.agents.independent_mode import IndependentMode
from app.utils.intent_classifier import IntentClassifier
from app.utils.LLM_agent_client import LLMAgentClient
from app.utils.Evaluator import evaluate_synthesis
import os

class Orchestrator:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.opposition_mode = OppositionMode()
        self.support_mode = SupportMode()
        self.independent_mode = IndependentMode()
        self.consensus_client = LLMAgentClient()
    
    def check_if_ai_needed(self, user_query: str, conversation_history: list = None) -> bool:
        """Fast gatekeeper check to prevent orchestrating idle chat."""
        context_str = self._build_context_str(conversation_history)
        return self.intent_classifier.should_invoke_ai(user_query, context_str)

    def execute_query(self, user_query: str, conversation_history: list = None, mode_override: str = None, status_callback=None, stream_callback=None) -> dict:
        """Main orchestration logic with conversation context"""
        
        context_str = self._build_context_str(conversation_history)
        
        # Step 1: Classify intent
        if mode_override:
            mode = mode_override
        else:
            if status_callback: status_callback("Classifying intent...")
            print("Classifying intent...")
            mode = self.intent_classifier.classify(user_query, context_str)
            print(f"Mode selected: {mode}")
        
        # Step 2: Execute appropriate mode
        if mode == "opposition":
            result = self.opposition_mode.run(user_query, context_str, status_callback)
        elif mode == "support":
            result = self.support_mode.run(user_query, context_str, status_callback)
        else:
            result = self.independent_mode.run(user_query, context_str, status_callback)
        
        # Step 3: Consensus synthesis
        if status_callback: status_callback("Synthesizing final consensus...")
        print("Synthesizing consensus...")
        final_answer = self.synthesize_consensus(user_query, result, context_str, mode, stream_callback=stream_callback)
        print("Complete!")
        
        # Step 4: Evaluate synthesis quality — prints scorecard to terminal
        evaluate_synthesis(
            user_query      = user_query,
            agent_responses = result["responses"],
            final_answer    = final_answer,
            mode            = mode,
            context_str     = context_str,
        )

        return {
            "mode_used": mode,
            "agent_responses": result["responses"],
            "final_answer": final_answer
        }

    def _build_context_str(self, conversation_history: list) -> str:
        """
        Converts conversation_history into a formatted string for agent prompts.
        Does NOT slice — context_builder already controls the window.
        Summary entry (from hybrid memory) is always kept at the top.
        """
        if not conversation_history:
            return ""

        parts = []
        for msg in conversation_history:
            name    = msg.get("name", msg.get("role", "unknown"))
            content = msg.get("content", "")
            parts.append(f"{name}: {content}")

        return "\n".join(parts)
    
    def synthesize_consensus(self, original_query: str, agent_results: dict, context_str: str = "", mode: str = "", stream_callback=None) -> str:
        """Synthesize final consensus from agent responses using streaming token dispatch."""
        # To avoid Groq TPM limit errors on free tiers, truncate long Opposition mode logs
        # We only pass the FINAL round (last 4 messages) to the synthesis agent
        if mode == "opposition" and len(agent_results.get("responses", [])) > 5:
            subset = agent_results["responses"][-4:]
            responses_text = "(Debate was very long. Showing only the final resolved round:)\n\n" + "\n\n".join([
                f"{r['agent_name']}: {r['content']}" 
                for r in subset
            ])
        else:
            responses_text = "\n\n".join([
                f"{r['agent_name']}: {r['content']}" 
                for r in agent_results["responses"]
            ])
        
        context_section = ""
        if context_str:
            context_section = f"""[Conversation Context — use ONLY if directly relevant to this specific query]:
{context_str}

"""

        mode_hint = {
            "opposition": "Agents debated this. Resolve the debate, correct errors, give the verified answer.",
            "support":    "Agents explained this sequentially. Combine into one complete, well-structured answer.",
            "independent":"Agents gave independent perspectives. Synthesize into one coherent answer without repetition.",
        }.get(mode, "")

        synthesis_prompt = f"""{context_section}User Query: {original_query}

Agent Responses:
{responses_text}

{f"Mode hint: {mode_hint}" if mode_hint else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You are the FINAL AI in a multi-agent group chat. You are the smartest agent.
Your job is to give the BEST possible final answer.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRICT INTELLIGENCE RULES:
1. MATCH YOUR RESPONSE LENGTH TO THE QUESTION.
   - Simple question → short, direct answer.
   - Deep technical question → full detailed answer with code/examples.
   - Essay request → full essay.
   - "Okay" / "thanks" / greeting → this should NOT reach you. If it does, respond in 1 line.

2. NEVER SUMMARIZE THE AGENT DISCUSSION unless there was a real debate/correction worth noting.
   - If agents agreed → just give the answer, don't mention they agreed.
   - If agents debated and corrected each other → briefly mention the correction, then give the right answer.
   - NEVER start with "The agents discussed..." or "Agent 1 said..." — users don't care.

3. CONTEXT USAGE — BE SMART:
   - Use conversation context ONLY if it genuinely helps answer this specific query.
   - If the user asks something completely new, IGNORE previous context entirely.
   - NEVER recap or summarize previous exchanges just because context exists.
   - Do NOT mention "based on our previous conversation" unless it's truly necessary.

4. FORMATTING:
   - Use headers/sections ONLY for long multi-part answers.
   - Use code blocks for ALL code — never inline plain text code.
   - Use bullet points only when listing genuinely distinct items.
   - No unnecessary padding, preamble, or filler phrases.

5. TONE: Sound like ChatGPT or Claude — confident, natural, intelligent. Not corporate, not robotic.

6. VERIFICATION — READ ALL AGENT RESPONSES BEFORE WRITING ANYTHING:
   - Before forming your answer, mentally cross-check every factual claim across all agents.
   - If Agent 1 says X and Agent 2 says Y on the same fact, determine which is correct based
     on your own knowledge. State the correct one. Do not average or hedge between two wrong options.
   - If all agents agree on something that is factually wrong, correct it. You are not bound
     by agent consensus — you are bound by accuracy.
   - Never repeat a claim just because an agent said it. You must independently validate it.

7. HALLUCINATION PREVENTION:
   - Only state facts you are confident are true. If uncertain, say so explicitly.
   - Do NOT add extra details, statistics, names, dates, or examples that were not in the
     agent responses AND that you cannot verify with high confidence.
   - If agents provided a specific number, date, or name — double-check it mentally before
     including it. If it feels wrong, flag it or omit it rather than repeat it blindly.
   - Prefer saying less with high confidence over saying more with low confidence.

8. YOUR ANSWER MUST BE STRICTLY BETTER THAN EVERY INDIVIDUAL AGENT RESPONSE:
   - Read all three agent responses. Your answer must be more accurate, more complete,
     and better structured than any single one of them.
   - Pick the best elements from each agent and combine them — never just copy one agent.
   - If one agent gave a great explanation but missed a key point another agent caught,
     your answer must include both.
   - If all agents gave a weak or incomplete answer, use your own knowledge to fill the gap.
     You are the final authority — not a reporter of what agents said.

Now give the final answer:"""

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are the smartest AI in a multi-agent system. You synthesize agent discussions into the single best possible final answer, adapting your length, tone, and format to exactly match what the question needs. You independently verify every fact before including it. You are the final authority on accuracy — not a summarizer of agent opinions."
                },
                {"role": "user", "content": synthesis_prompt}
            ]

            # agent5 = meta-llama/llama-4-scout-17b-16e-instruct (streaming internally, returns full string)
            return self.consensus_client.get_completion(
                "agent5",
                messages,
                max_tokens=4096,
                stream_callback=stream_callback
            )
            
        except Exception as e:
            return f"Error in synthesis: {e}"