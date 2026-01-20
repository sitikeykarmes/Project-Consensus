from groq import Groq
import os

class IntentClassifier:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    def classify(self, user_query: str) -> str:
        """
        Classify user intent into: opposition, support, or independent
        """
        system_prompt = """You are an intent classifier. Analyze the user query and classify it into ONE of these modes:
        
        - opposition: When the query needs fact-checking, verification, or critical analysis. 
          Examples: "Is climate change real?", "Verify this claim", "What are the flaws in this argument?"
        
        - support: When the query needs deep explanation, context, or comprehensive information.
          Examples: "Explain quantum computing in detail", "What are all the benefits of exercise?"
        
        - independent: When the query asks for comparisons, multiple viewpoints, or diverse perspectives.
          Examples: "Compare Python vs JavaScript", "What are different opinions on AI?", "Pros and cons of remote work"
        
        Respond with ONLY ONE WORD: opposition, support, or independent"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify this query: {user_query}"}
                ],
                temperature=0,
                max_tokens=10
            )
            
            mode = response.choices[0].message.content.strip().lower()
            
            # Default to support if unclear
            if mode not in ["opposition", "support", "independent"]:
                mode = "support"
            
            return mode
        except Exception as e:
            print(f"Error in intent classification: {e}")
            return "support"  # Default fallback
