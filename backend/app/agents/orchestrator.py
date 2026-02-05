# backend/app/agents/orchestrator.py
from app.agents.opposition_mode import OppositionMode
from app.agents.support_mode import SupportMode
from app.agents.independent_mode import IndependentMode
from app.utils.intent_classifier import IntentClassifier
from app.utils.LLM_agent_client import LLMAgentClient
import os

class Orchestrator:
    def __init__(self):
        self.intent_classifier = IntentClassifier()  # Uses Groq
        self.opposition_mode = OppositionMode()
        self.support_mode = SupportMode()
        self.independent_mode = IndependentMode()
        self.consensus_client = LLMAgentClient()  # Use OpenRouter for consensus
    
    def execute_query(self, user_query: str, mode_override: str = None) -> dict:
        """Main orchestration logic"""
        
        # Step 1: Classify intent or use override (uses Groq)
        if mode_override:
            mode = mode_override
        else:
            print("🔍 Classifying intent...")
            mode = self.intent_classifier.classify(user_query)
            print(f"📋 Mode selected: {mode}")
        
        # Step 2: Execute appropriate mode (uses OpenRouter models)
        if mode == "opposition":
            result = self.opposition_mode.run(user_query)
        elif mode == "support":
            result = self.support_mode.run(user_query)
        else:  # independent
            result = self.independent_mode.run(user_query)
        
        # Step 3: Consensus synthesis (uses OpenRouter)
        print("🔄 Synthesizing consensus...")
        final_answer = self.synthesize_consensus(user_query, result)
        print("✅ Complete!")
        
        return {
            "mode_used": mode,
            "agent_responses": result["responses"],
            "final_answer": final_answer
        }
    
    def synthesize_consensus(self, original_query: str, agent_results: dict) -> str:
        """Synthesize final consensus from agent responses using Gemini Flash"""
        responses_text = "\n\n".join([
            f"{r['agent_name']}: {r['content']}" 
            for r in agent_results["responses"]
        ])
        
        synthesis_prompt = f"""User Query: {original_query}

Agent Responses:
{responses_text}

You are the final assistant in a WhatsApp group chat.

Task:
- Summarize the key takeaway from the agent discussion.
- Mention if any correction/debate happened.
- Give ONE short final answer until asked for longer answer.

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