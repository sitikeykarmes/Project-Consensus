# backend/app/agents/opposition_mode.py
from app.utils.LLM_agent_client import LLMAgentClient

class OppositionMode:
    def __init__(self):
        self.client = LLMAgentClient()
    
    def generator_agent(self, user_query: str) -> str:
        """Generate initial response using Agent 1"""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Provide a clear, factual answer to the user's question."},
                {"role": "user", "content": user_query}
            ]
            
            return self.client.get_completion("agent1", messages, temperature=0.7, max_tokens=500)
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def critic_agent(self, user_query: str, generator_response: str) -> str:
        """Critique the generator's response using Agent 2"""
        try:
            critique_prompt = f"""Original Query: {user_query}

Generator's Response: {generator_response}

You are a critical fact-checker and red team agent. Your job is to identify:
1. Factual errors or inaccuracies
2. Logical fallacies
3. Missing important context
4. Potential hallucinations

If the response is accurate, acknowledge it. If there are issues, explain them clearly.

Provide your critical analysis:"""

            messages = [
                {"role": "system", "content": "You are a critical fact-checker. Analyze responses for accuracy and completeness."},
                {"role": "user", "content": critique_prompt}
            ]
            
            return self.client.get_completion("agent2", messages, temperature=0.3, max_tokens=500)
            
        except Exception as e:
            return f"Error in critique: {str(e)}"
    
    def run(self, user_query: str) -> dict:
        """Execute opposition mode workflow"""
        print("🤖 Running Opposition Mode...")
        
        generator_response = self.generator_agent(user_query)
        print(f"✓ Generator (Agent 1) completed")
        
        critic_response = self.critic_agent(user_query, generator_response)
        print(f"✓ Critic (Agent 2) completed")
        
        return {
            "mode": "opposition",
            "responses": [
                {
                    "agent_name": "Generator (Agent 1)",
                    "content": generator_response,
                    "mode": "opposition"
                },
                {
                    "agent_name": "Critic (Agent 2)",
                    "content": critic_response,
                    "mode": "opposition"
                }
            ]
        }