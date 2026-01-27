# backend/app/agents/support_mode.py
from app.utils.openrouter_client import OpenRouterClient

class SupportMode:
    def __init__(self):
        self.client = OpenRouterClient()
    
    def lead_agent(self, user_query: str) -> str:
        """Create initial draft using Agent 1"""
        try:
            messages = [
                {"role": "system", "content": "You are a lead researcher. Provide a comprehensive initial answer."},
                {"role": "user", "content": user_query}
            ]
            
            return self.client.get_completion("agent1", messages, temperature=0.7, max_tokens=500)
            
        except Exception as e:
            return f"Error in lead agent: {str(e)}"
    
    def supplementer_agent(self, user_query: str, lead_response: str) -> str:
        """Enrich the initial response using Agent 2"""
        try:
            supplement_prompt = f"""Original Query: {user_query}

Lead Agent's Response: {lead_response}

You are a supplementer agent. Your job is to:
1. Add additional context and details
2. Provide examples or analogies
3. Cover angles the lead agent might have missed
4. Ensure comprehensive coverage

Build upon the lead agent's response to make it richer:"""

            messages = [
                {"role": "system", "content": "You are a supplementer. Add depth and additional perspectives to existing responses."},
                {"role": "user", "content": supplement_prompt}
            ]
            
            return self.client.get_completion("agent2", messages, temperature=0.7, max_tokens=500)
            
        except Exception as e:
            return f"Error in supplementer: {str(e)}"
    
    def run(self, user_query: str) -> dict:
        """Execute support mode workflow"""
        print("🤖 Running Support Mode...")
        
        lead_response = self.lead_agent(user_query)
        print(f"✓ Lead Agent (Agent 1) completed")
        
        supplement_response = self.supplementer_agent(user_query, lead_response)
        print(f"✓ Supplementer (Agent 2) completed")
        
        return {
            "mode": "support",
            "responses": [
                {
                    "agent_name": "Lead Agent (Agent 1)",
                    "content": lead_response,
                    "mode": "support"
                },
                {
                    "agent_name": "Supplementer (Agent 2)",
                    "content": supplement_response,
                    "mode": "support"
                }
            ]
        }