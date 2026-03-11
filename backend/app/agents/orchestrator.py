# backend/app/agents/orchestrator.py
from app.agents.opposition_mode import OppositionMode
from app.agents.support_mode import SupportMode
from app.agents.independent_mode import IndependentMode
from app.utils.intent_classifier import IntentClassifier
from app.utils.LLM_agent_client import LLMAgentClient
import os

class Orchestrator:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.opposition_mode = OppositionMode()
        self.support_mode = SupportMode()
        self.independent_mode = IndependentMode()
        self.consensus_client = LLMAgentClient()
    
    def execute_query(self, user_query: str, conversation_history: list = None, mode_override: str = None) -> dict:
        """Main orchestration logic with conversation context"""
        
        context_str = self._build_context_str(conversation_history)
        
        # Step 1: Classify intent
        if mode_override:
            mode = mode_override
        else:
            print("Classifying intent...")
            mode = self.intent_classifier.classify(user_query, context_str)
            print(f"Mode selected: {mode}")
        
        # Step 2: Execute appropriate mode
        if mode == "opposition":
            result = self.opposition_mode.run(user_query, context_str)
        elif mode == "support":
            result = self.support_mode.run(user_query, context_str)
        else:
            result = self.independent_mode.run(user_query, context_str)
        
        # Step 3: Consensus synthesis
        print("Synthesizing consensus...")
        final_answer = self.synthesize_consensus(user_query, result, context_str)
        print("Complete!")
        
        return {
            "mode_used": mode,
            "agent_responses": result["responses"],
            "final_answer": final_answer
        }

    def _build_context_str(self, conversation_history: list) -> str:
        """
        Converts conversation_history into a formatted string for agent prompts.

        Handles two types of entries passed by context_builder:
          - Summary entry:  {"name": "Context Summary", "content": "[Summary of earlier...]"}
          - Regular entry:  {"name": "user@email.com",  "content": "..."}

        Does NOT slice — the hybrid context builder already controls the window.
        Summary is always first, followed by recent verbatim messages.
        """
        if not conversation_history:
            return ""

        parts = []
        for msg in conversation_history:
            name    = msg.get("name", msg.get("role", "unknown"))
            content = msg.get("content", "")
            parts.append(f"{name}: {content}")

        return "\n".join(parts)
    
    def synthesize_consensus(self, original_query: str, agent_results: dict, context_str: str = "") -> str:
        """Synthesize final consensus from agent responses using agent4 (qwen/qwen3-32b)"""
        responses_text = "\n\n".join([
            f"{r['agent_name']}: {r['content']}" 
            for r in agent_results["responses"]
        ])
        
        context_section = ""
        if context_str:
            context_section = f"""Previous Conversation Context:
{context_str}

"""
        
        synthesis_prompt = f"""{context_section}User Query: {original_query}

Agent Responses:
{responses_text}

You are the final assistant in a Multi-User Multi-AI group chat.
Guidelines:
- Do NOT always summarize.
- If greeting → respond naturally.
- If code → provide full working code.
- If essay → provide full essay.
- If explanation → give detailed explanation.
- If said "okay" or "thanks" → no need to repeat or summarize in detail, just acknowledge naturally in short.

Task:
- Summarize the key takeaway from the agent discussion when you think is needed otherwise just give Final Answer, but dont mention the words Final Answer.
- Mention if any correction/debate happened, Mention only if happened, otherwise no need to mention about debate/correction.
- Consider the previous conversation context if available or if relevant.
- Give a concise, clear, and coherent final answer that addresses the user's query based on the agent responses and context.

Rules:
- Give Headings and formatting only when useful.
- Sound Natural and Intelligent and like Top-Tier AI assistants - ChatGPT/Gemini.

Be concise. Synthesize a final consensus answer:"""

        try:
            messages = [
                {"role": "system", "content": "You are a synthesis expert. Combine multiple perspectives into one coherent answer."},
                {"role": "user", "content": synthesis_prompt}
            ]

            return self.consensus_client.get_completion("agent4", messages, max_tokens=4096)
            
        except Exception as e:
            return f"Error in synthesis: {e}"