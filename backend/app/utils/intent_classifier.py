from groq import Groq
import os

class IntentClassifier:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    def classify(self, user_query: str) -> str:
        """
        Classifies user intent into one of three project orchestration modes:
        - independent (Comparison Mode)
        - support (Supplement Mode)
        - opposition (Debate Mode)
        """
        
        system_prompt = """You are the Intent Classification Engine for 'Project Consensus'. 
Your task is to route a user query to the correct multi-agent collaboration strategy.

### 1. INDEPENDENT (Comparison Mode)
- **Purpose**: Diverse perspectives and brainstorming [cite: 265-266].
- **Select when**: The user asks for comparisons, pros/cons, or multiple alternatives[cite: 264].
- **Trigger Phrases**: "Compare...", "What are the differences...", "Give me options...", "Brainstorm...".
- **Examples**:
    1. Compare React vs Vue for performance.
    2. What are the differences between 5G and 6G?
    3. Give me 10 ideas for a sci-fi novel.
    4. Pros and cons of electric vehicles.
    5. Compare the economy of India vs China.
    [... Include 45+ similar comparison/brainstorming queries ...]

### 2. SUPPORT (Supplement Mode)
- **Purpose**: Deep explanation and comprehensive context[cite: 187].
- **Select when**: The topic is established/non-debatable and needs a detailed guide or tutorial.
- **Trigger Phrases**: "Explain how...", "Tutorial for...", "What are the benefits of...", "Guide to...".
- **Examples**:
    1. Explain how a blockchain works step-by-step.
    2. What are the benefits of daily meditation?
    3. How to set up a FastAPI server?
    4. Technical walkthrough of a jet engine.
    5. Detailed history of the Roman Empire.
    [... Include 45+ similar deep-dive/tutorial queries ...]

### 3. OPPOSITION (Debate Mode)
- **Purpose**: Fact-checking, active opposition, and revealing weaknesses [cite: 192-193].
- **Select when**: The query is a factual claim needing verification, a controversial topic, or a request for critique [cite: 278-281].
- **Trigger Phrases**: "Is it true that...", "Verify if...", "Fact-check...", "Critique this...", "Debate...".
- **Examples**:
    1. Does drinking cold water cause cancer? (Controversial/Verification needed)
    2. Is climate change a hoax? (Debatable/Red-team needed)
    3. Verify the claim that AI will reach singularity by 2030.
    4. Critique the logic in this argument for flat earth.
    5. Is the moon landing real? (Verification request)
    [... Include 45+ similar fact-checking/controversial queries ...]

### DECISION LOGIC:
- If it's "This vs That" or "Give me ideas" -> independent.
- If it's "Teach me how this works" or "Explain the history" -> support.
- If it's "Is this true?", "Verify this", or "Debate this" -> opposition.

Respond with ONLY ONE WORD: independent, support, or opposition."""
        
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
            
            if mode not in ["opposition", "support", "independent"]:
                mode = "independent" # Default fallback
            
            return mode
        except Exception as e:
            print(f"Error in intent classification: {e}")
            return "independent"