# backend/app/utils/intent_classifier.py
from groq import Groq
import os

class IntentClassifier:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
    
    def classify(self, user_query: str, context: str = "") -> str:
        """
        Classifies user intent into one of three multi-agent orchestration modes:
        - independent (Comparison Mode): Parallel diverse perspectives
        - support (Supplement Mode): Sequential verification and enrichment
        - opposition (Debate Mode): Adversarial fact-checking and critique
        """
        
        system_prompt = """You are the Intent Classification Engine for the Multi-Agent AI Collaboration Platform.
Your task is to analyze user queries and route them to the optimal multi-agent orchestration mode.

## THREE ORCHESTRATION MODES:

### 1. INDEPENDENT (Comparison Mode)
**Purpose:** Get diverse perspectives quickly through parallel AI responses
**When to Select:**
- User asks for comparisons or alternatives
- Need multiple viewpoints or options
- Brainstorming and idea generation
- Exploring different approaches
- "What are the differences..." type questions

**Trigger Phrases:**
- "Compare...", "versus", "vs"
- "What are the differences between..."
- "Give me options for..."
- "What are different approaches to..."
- "Pros and cons of..."
- "Which is better..."
- "Alternatives to..."
- "Ideas for..."
- "Suggest multiple..."

**Example Queries:**
1. Compare React vs Vue vs Angular for web development
2. What are the differences between MySQL and PostgreSQL?
3. Give me 10 ideas for a science fiction novel
4. Pros and cons of remote work vs office work
5. Which programming language is better for AI: Python or R?
6. Compare electric vehicles vs hybrid vs gasoline cars
7. What are different approaches to machine learning?
8. Suggest multiple frameworks for building APIs
9. iPhone vs Android: which should I choose?
10. Compare capitalism vs socialism economic systems
11. What are alternatives to Amazon AWS?
12. Different investment strategies for beginners
13. Compare NoSQL databases: MongoDB, Cassandra, Redis
14. What are various meditation techniques?
15. Marketing strategies: social media vs traditional advertising
16. Compare cloud providers: AWS vs Azure vs GCP
17. Different types of neural networks and their uses
18. Startup funding options: VC vs bootstrapping vs angel investors
19. Compare frontend frameworks for modern web apps
20. What are different agile methodologies?

### 2. SUPPORT (Supplement Mode)
**Purpose:** Deep, verified explanation through sequential enrichment
**When to Select:**
- User needs comprehensive explanation
- Tutorial or how-to requests
- Factual information that needs depth
- Step-by-step guides
- Established topics (not controversial)

**Trigger Phrases:**
- "Explain how...", "How does... work"
- "Tutorial for...", "Guide to..."
- "What are the benefits of..."
- "Step-by-step..."
- "Teach me about..."
- "What is... (detailed explanation)"
- "How to..."
- "Walk me through..."

**Example Queries:**
1. Explain how blockchain technology works step-by-step
2. What are the benefits of daily meditation practice?
3. How to set up a FastAPI server with PostgreSQL?
4. Tutorial for building a REST API from scratch
5. Explain how a jet engine works
6. Detailed history of the Roman Empire
7. How does photosynthesis work at molecular level?
8. Guide to implementing OAuth2 authentication
9. What is quantum computing and how does it work?
10. Explain the process of protein synthesis in cells
11. How to train a neural network for image classification?
12. What are the health benefits of intermittent fasting?
13. Step-by-step guide to deploy a Docker container
14. Explain how HTTP requests work in detail
15. Tutorial for React hooks: useState, useEffect, useContext
16. How does the human immune system fight viruses?
17. Comprehensive guide to Git branching strategies
18. What is the theory of relativity explained simply?
19. How to implement JWT authentication in Node.js?
20. Explain the water cycle in Earth's ecosystem

### 3. OPPOSITION (Debate Mode)
**Purpose:** Fact-checking through adversarial debate and critique
**When to Select:**
- Verification of factual claims needed
- Controversial or debatable topics
- User asks to critique or fact-check
- Claims that sound questionable
- "Is it true that..." questions
- Ethical or political debates

**Trigger Phrases:**
- "Is it true that...", "Is this claim valid..."
- "Fact-check...", "Verify if..."
- "Critique this...", "What's wrong with..."
- "Debate...", "Argue for and against..."
- "Is [controversial claim]..."
- "Challenge this idea..."
- "Does [questionable claim]..."

**Example Queries:**
1. Is it true that drinking cold water causes cancer?
2. Fact-check: Does AI will reach singularity by 2030?
3. Is climate change a hoax? (Debate this claim)
4. Verify if vaccines cause autism
5. Critique the logic in flat earth arguments
6. Is the moon landing fake?
7. Does 5G cause COVID-19? Fact-check this
8. Debate: Is capitalism better than socialism?
9. Is it true that humans only use 10% of their brains?
10. Fact-check: Do we live in a simulation?
11. Critique the claim that all AI will become sentient
12. Is nuclear energy safer than solar energy?
13. Verify: Can you manifest reality with your thoughts?
14. Debate whether social media does more harm than good
15. Is it true that coffee stunts growth?
16. Fact-check: Does eating fat make you fat?
17. Critique the argument for banning cryptocurrency
18. Is homeopathy scientifically valid?
19. Verify the claim that GMOs are dangerous
20. Debate: Should AI research be regulated by government?

## DECISION LOGIC:

**Choose INDEPENDENT when:**
- Query contains comparison keywords (vs, compare, differences, alternatives)
- User wants multiple options or perspectives
- Brainstorming or exploration needed
- "Which is better" type questions

**Choose SUPPORT when:**
- Query asks "how to" or "explain"
- Tutorial or educational content needed
- Deep dive into established/non-controversial topics
- Step-by-step guidance required
- User wants comprehensive understanding

**Choose OPPOSITION when:**
- Query asks "is it true", "verify", "fact-check"
- Controversial or debatable claim present
- User explicitly asks for critique or debate
- Claims that need adversarial verification
- Ethical, political, or controversial topics

## RESPONSE FORMAT:
Respond with EXACTLY ONE WORD (lowercase): independent, support, or opposition

No explanation, no punctuation, just the mode name."""

        try:
            context_prefix = ("Previous context:\n" + context + "\n\n") if context else ""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{context_prefix}Classify this query: {user_query}"}
                ],
                temperature=0.0,
                max_tokens=10
            )
            
            mode = response.choices[0].message.content.strip().lower()
            
            # Validate response
            valid_modes = ["independent", "support", "opposition"]
            if mode not in valid_modes:
                print(f"⚠️  Invalid classification '{mode}', defaulting to 'independent'")
                return "independent"
            
            return mode
            
        except Exception as e:
            print(f"❌ Error in intent classification: {e}")
            print("⚠️  Defaulting to 'independent' mode")
            return "independent"
    
    def classify_with_confidence(self, user_query: str) -> dict:
        """
        Classify with confidence score (optional advanced method)
        Returns: {"mode": str, "confidence": float, "reasoning": str}
        """
        
        detailed_prompt = f"""Classify this query and provide reasoning:

Query: "{user_query}"

Provide your response in this exact format:
MODE: [independent/support/opposition]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Follow the format exactly."},
                    {"role": "user", "content": detailed_prompt}
                ],
                temperature=0.0,
                max_tokens=100
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse response
            lines = content.split('\n')
            mode = "independent"
            confidence = 0.8
            reasoning = "Default classification"
            
            for line in lines:
                if line.startswith("MODE:"):
                    mode = line.split(":")[-1].strip().lower()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":")[-1].strip())
                    except:
                        confidence = 0.8
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[-1].strip()
            
            # Validate mode
            if mode not in ["independent", "support", "opposition"]:
                mode = "independent"
            
            return {
                "mode": mode,
                "confidence": confidence,
                "reasoning": reasoning
            }
            
        except Exception as e:
            print(f"❌ Error in detailed classification: {e}")
            return {
                "mode": "independent",
                "confidence": 0.5,
                "reasoning": "Error occurred, using default"
            }