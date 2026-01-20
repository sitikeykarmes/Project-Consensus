from groq import Groq
import os

class OppositionMode:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
    
    def generator_agent(self, user_query: str) -> str:
        """Generate initial response"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Provide a clear, factual answer to the user's question."},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {e}"
    
    def critic_agent(self, user_query: str, generator_response: str) -> str:
        """Critique the generator's response"""
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

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a critical fact-checker. Analyze responses for accuracy and completeness."},
                    {"role": "user", "content": critique_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in critique: {e}"
    
    def run(self, user_query: str) -> dict:
        """Execute opposition mode workflow"""
        print("🤖 Running Opposition Mode...")
        
        # Step 1: Generator creates response
        generator_response = self.generator_agent(user_query)
        print(f"✓ Generator completed")
        
        # Step 2: Critic analyzes response
        critic_response = self.critic_agent(user_query, generator_response)
        print(f"✓ Critic completed")
        
        return {
            "mode": "opposition",
            "responses": [
                {
                    "agent_name": "Generator",
                    "content": generator_response,
                    "mode": "opposition"
                },
                {
                    "agent_name": "Critic",
                    "content": critic_response,
                    "mode": "opposition"
                }
            ]
        }
