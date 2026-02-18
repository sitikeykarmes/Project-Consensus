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
        
        # Build context string from history
        context_str = ""
        if conversation_history:
            context_parts = []
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                name = msg.get("name", role)
                context_parts.append(f"{name}: {content}")
            context_str = "\n".join(context_parts)
        
        # Step 1: Classify intent (with context)
        if mode_override:
            mode = mode_override
        else:
            print("Classifying intent...")
            mode = self.intent_classifier.classify(user_query, context_str)
            print(f"Mode selected: {mode}")
        
        # Step 2: Execute appropriate mode (with context)
        if mode == "opposition":
            result = self.opposition_mode.run(user_query, context_str)
        elif mode == "support":
            result = self.support_mode.run(user_query, context_str)
        else:
            result = self.independent_mode.run(user_query, context_str)
        
        # Step 3: Consensus synthesis (with context)
        print("Synthesizing consensus...")
        final_answer = self.synthesize_consensus(user_query, result, context_str)
        print("Complete!")
        
        return {
            "mode_used": mode,
            "agent_responses": result["responses"],
            "final_answer": final_answer
        }
    
    def synthesize_consensus(self, original_query: str, agent_results: dict, context_str: str = "") -> str:
        """Synthesize final consensus from agent responses"""
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

You are the final assistant in a WhatsApp group chat.

Task:
- Summarize the key takeaway from the agent discussion.
- Mention if any correction/debate happened.
- Give ONE short final answer until asked for longer answer.
- Consider the previous conversation context if available.

Rules:
- Max 4 lines until asked beyond this limit.
- Give Headings and formatting.
- Sound like ChatGPT/Gemini.

Be concise. Synthesize a final consensus answer:"""

        try:
            messages = [
                {"role": "system", "content": "You are a synthesis expert. Combine multiple perspectives into one coherent answer."},
                {"role": "user", "content": synthesis_prompt}
            ]
            
            return self.consensus_client.get_completion("agent3", messages, temperature=0.3, max_tokens=600)
            
        except Exception as e:
            return f"Error in synthesis: {e}"
