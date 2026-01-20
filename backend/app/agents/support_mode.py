from groq import Groq
import os

class SupportMode:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
    
    def lead_agent(self, user_query: str) -> str:
        """Create initial draft"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a lead researcher. Provide a comprehensive initial answer."},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in lead agent: {e}"
    
    def supplementer_agent(self, user_query: str, lead_response: str) -> str:
        """Enrich the initial response"""
        try:
            supplement_prompt = f"""Original Query: {user_query}

Lead Agent's Response: {lead_response}

You are a supplementer agent. Your job is to:
1. Add additional context and details
2. Provide examples or analogies
3. Cover angles the lead agent might have missed
4. Ensure comprehensive coverage

Build upon the lead agent's response to make it richer:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a supplementer. Add depth and additional perspectives to existing responses."},
                    {"role": "user", "content": supplement_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in supplementer: {e}"
    
    def run(self, user_query: str) -> dict:
        """Execute support mode workflow"""
        print("🤖 Running Support Mode...")
        
        # Step 1: Lead agent creates initial response
        lead_response = self.lead_agent(user_query)
        print(f"✓ Lead Agent completed")
        
        # Step 2: Supplementer enriches it
        supplement_response = self.supplementer_agent(user_query, lead_response)
        print(f"✓ Supplementer completed")
        
        return {
            "mode": "support",
            "responses": [
                {
                    "agent_name": "Lead Agent",
                    "content": lead_response,
                    "mode": "support"
                },
                {
                    "agent_name": "Supplementer",
                    "content": supplement_response,
                    "mode": "support"
                }
            ]
        }
