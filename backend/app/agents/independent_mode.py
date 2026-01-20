from groq import Groq
import os

class IndependentMode:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
    
    def agent_1(self, user_query: str) -> dict:
        """First independent perspective"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Agent 1. Provide your unique perspective on the query. Be opinionated but fair."},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.8,
                max_tokens=400
            )
            return {
                "agent_name": "Agent 1",
                "content": response.choices[0].message.content,
                "mode": "independent"
            }
        except Exception as e:
            return {
                "agent_name": "Agent 1",
                "content": f"Error: {e}",
                "mode": "independent"
            }
    
    def agent_2(self, user_query: str) -> dict:
        """Second independent perspective"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Agent 2. Provide a different perspective. Emphasize different aspects than Agent 1 would."},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.8,
                max_tokens=400
            )
            return {
                "agent_name": "Agent 2",
                "content": response.choices[0].message.content,
                "mode": "independent"
            }
        except Exception as e:
            return {
                "agent_name": "Agent 2",
                "content": f"Error: {e}",
                "mode": "independent"
            }
    
    def agent_3(self, user_query: str) -> dict:
        """Third independent perspective"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Agent 3. Provide yet another unique angle. Consider aspects others might miss."},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.8,
                max_tokens=400
            )
            return {
                "agent_name": "Agent 3",
                "content": response.choices[0].message.content,
                "mode": "independent"
            }
        except Exception as e:
            return {
                "agent_name": "Agent 3",
                "content": f"Error: {e}",
                "mode": "independent"
            }
    
    def run(self, user_query: str) -> dict:
        """Execute all agents sequentially"""
        print("🤖 Running Independent Mode...")
        
        results = []
        
        # Run agents sequentially
        result1 = self.agent_1(user_query)
        print(f"✓ Agent 1 completed")
        results.append(result1)
        
        result2 = self.agent_2(user_query)
        print(f"✓ Agent 2 completed")
        results.append(result2)
        
        result3 = self.agent_3(user_query)
        print(f"✓ Agent 3 completed")
        results.append(result3)
        
        return {
            "mode": "independent",
            "responses": results
        }
