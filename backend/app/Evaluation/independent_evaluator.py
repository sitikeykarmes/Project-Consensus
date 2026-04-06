# backend/app/Evaluation/independent_evaluator.py
import json
import os
from groq import Groq

def evaluate_independent(user_query: str, agent_responses: list, final_answer: str, generic_metrics: dict) -> dict:
    """
    Independent Mode — Primary Strength: Perspective Diversity
    Calculates: Independent Score = 0.40×PDS + 0.30×Comprehensiveness + 0.30×AgentCoverage − FalseConsensusPenalty
    """
    import groq
    client = groq.Groq(api_key=os.getenv("consensus_test_1"))
    agents_text = "\n\n".join(f"[{r.get('agent_name', 'Agent')}]: {r.get('content', '')}" for r in agent_responses)

    prompt = f"""You are a strict AI evaluation judge scoring an Independent Brainstorming Mode synthesis.
    
USER QUERY: {user_query}

AGENT RESPONSES:
{agents_text}

FINAL SYNTHESIZED ANSWER:
{final_answer}

Score the following metrics strictly on a scale of 0.0 to 10.0:
1. "PDS" (Perspective Diversity Score): How well does the synthesis cover the diverse range of unique perspectives provided by the agents? (0.0 to 10.0)
2. "Comprehensiveness": How thoroughly did the synthesis capture all valid ideas without arbitrarily dropping points? (0.0 to 10.0)
3. "FalseConsensusPenalty": Did the synthesis falsely claim the agents agreed on everything when they actually had divergent ideas? (Penalty: 0.0 to 2.0. 0.0 means no false consensus, 2.0 means severe false consensus).

Respond exactly with a valid JSON object matching this schema (replace the example values with your actual calculated scores):
{{
  "PDS": <Float between 0.0 and 10.0>,
  "Comprehensiveness": <Float between 0.0 and 10.0>,
  "FalseConsensusPenalty": <Float between 0.0 and 2.0>
}}
"""
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are a stringent JSON-only judge."}, {"role": "user", "content": prompt}],
            temperature=0.0
        )
    except groq.APIStatusError as e:
        if e.status_code == 429:
            print("  [>] Rate Limit on consensus_test_1. Falling back to consensus_test_2...")
            client = groq.Groq(api_key=os.getenv("consensus_test_2"))
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "You are a stringent JSON-only judge."}, {"role": "user", "content": prompt}],
                    temperature=0.0
                )
            except groq.APIStatusError as e2:
                if e2.status_code == 429:
                    print("  [>] Rate Limit on consensus_test_2. Falling back to consensus_test_3...")
                    client = groq.Groq(api_key=os.getenv("consensus_test_3"))
                    try:
                        resp = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": "You are a stringent JSON-only judge."}, {"role": "user", "content": prompt}],
                            temperature=0.0
                        )
                    except Exception as e3:
                        print(f"Independent Evaluator failed on 3rd fallback key: {e3}")
                        return {}
                else:
                    return {}
            except Exception as e2:
                print(f"Independent Evaluator failed on 2nd fallback key: {e2}")
                return {}
        else:
            return {}
    except Exception as e:
        return {}
        
    try:
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"): raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
        data = json.loads(raw.strip())
        
        # Generic metric 'AgentCoverage' comes from the 0-1 scaled score
        agent_coverage = generic_metrics.get("agent_coverage", {}).get("fused", 0.8) * 10.0
        
        pds = data.get("PDS", 5.0)
        comprehensive = data.get("Comprehensiveness", 5.0)
        penalty = data.get("FalseConsensusPenalty", 0.0)
        
        final_score = (0.40 * pds) + (0.30 * comprehensive) + (0.30 * agent_coverage) - penalty
        final_score = max(0.0, min(10.0, final_score))
        
        return {
            "PDS": round(pds, 2),
            "Comprehensiveness": round(comprehensive, 2),
            "AgentCoverage": round(agent_coverage, 2),
            "FalseConsensusPenalty": round(penalty, 2),
            "Final_Independent_Score": round(final_score, 2)
        }
    except Exception as e:
        print(f"Independent Evaluator JSON parse failed: {e}")
        return {}
