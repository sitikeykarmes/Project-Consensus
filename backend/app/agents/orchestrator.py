from app.agents.opposition_mode import OppositionMode
from app.agents.support_mode import SupportMode
from app.agents.independent_mode import IndependentMode
from app.utils.intent_classifier import IntentClassifier
from groq import Groq
import os

class Orchestrator:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.opposition_mode = OppositionMode()
        self.support_mode = SupportMode()
        self.independent_mode = IndependentMode()
        self.consensus_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    def execute_query(self, user_query: str, mode_override: str = None) -> dict:
        """Main orchestration logic"""
        
        # Step 1: Classify intent or use override
        if mode_override:
            mode = mode_override
        else:
            print("🔍 Classifying intent...")
            mode = self.intent_classifier.classify(user_query)
            print(f"📋 Mode selected: {mode}")
        
        # Step 2: Execute appropriate mode
        if mode == "opposition":
            result = self.opposition_mode.run(user_query)
        elif mode == "support":
            result = self.support_mode.run(user_query)
        else:  # independent
            result = self.independent_mode.run(user_query)
        
        # Step 3: Consensus synthesis
        print("🔄 Synthesizing consensus...")
        final_answer = self.synthesize_consensus(user_query, result)
        print("✅ Complete!")
        
        return {
            "mode_used": mode,
            "agent_responses": result["responses"],
            "final_answer": final_answer
        }
    
    def synthesize_consensus(self, original_query: str, agent_results: dict) -> str:
        """Synthesize final consensus from agent responses"""
        responses_text = "\n\n".join([
            f"{r['agent_name']}: {r['content']}" 
            for r in agent_results["responses"]
        ])
        
        synthesis_prompt = f"""Original Query: {original_query}

Agent Responses:
{responses_text}

You are a consensus synthesizer. Your job is to:
1. Analyze all agent responses
2. Identify key points of agreement
3. Address any contradictions
4. Produce a final, verified answer that incorporates the best insights

Be concise but comprehensive. Synthesize a final consensus answer:"""

        try:
            response = self.consensus_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a synthesis expert. Combine multiple perspectives into one coherent answer."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in synthesis: {e}"
