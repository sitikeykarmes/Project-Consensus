# backend/app/Evaluation/opposition_evaluator.py
import json
import os
from groq import Groq

def evaluate_opposition(user_query: str, agent_responses: list, final_answer: str, generic_metrics: dict) -> dict:
    """
    Opposition Mode — Primary Strength: Accuracy and Error Correction
    Calculates: Opposition Score = 0.40×FactualConsistency + 0.35×EDR + 0.25×Faithfulness − HallucinationRate
    """
    import groq
    client = groq.Groq(api_key=os.getenv("consensus_test_1"))
    agents_text = "\n\n".join(f"[{r.get('agent_name', 'Agent')}]: {r.get('content', '')}" for r in agent_responses)

    prompt = f"""You are a strict AI evaluation judge scoring a multi-round Debate (Opposition) synthesis.
    
USER QUERY: {user_query}

DEBATE TRANSCRIPT (Generator vs Critic vs Judge):
{agents_text}

FINAL SYNTHESIZED ANSWER:
{final_answer}

Score the following metrics strictly on a scale of 0.0 to 10.0:
1. "FactualConsistency": Is the final synthesis perfectly consistent with the Chief Judge's established facts and verdict without contradicting them? (0.0 to 10.0)
2. "EDR" (Error Detection Rate): Did the synthesis explicitly point out and correct the errors that were argued over in the debate? (0.0 to 10.0)
3. "HallucinationRate": Did the synthesis hallucinate entire new fake facts or fake verdicts that were never mentioned by the Chief Judge? (Penalty: 0.0 to 2.0. 0.0 means totally grounded, 2.0 means severe hallucination).

Respond exactly with a valid JSON object matching this schema (replace the example values with your actual calculated scores):
{{
  "FactualConsistency": <Float between 0.0 and 10.0>,
  "EDR": <Float between 0.0 and 10.0>,
  "HallucinationRate": <Float between 0.0 and 2.0>
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
                        print(f"Opposition Evaluator failed on 3rd fallback key: {e3}")
                        return {}
                else:
                    return {}
            except Exception as e2:
                print(f"Opposition Evaluator failed on 2nd fallback key: {e2}")
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
        
        # Generic metric 'Faithfulness' comes from 0-1 scale
        faithfulness = generic_metrics.get("faithfulness", {}).get("fused", 0.8) * 10.0
        
        factual_const = data.get("FactualConsistency", 5.0)
        edr = data.get("EDR", 5.0)
        hallucination = data.get("HallucinationRate", 0.0)
        
        final_score = (0.40 * factual_const) + (0.35 * edr) + (0.25 * faithfulness) - hallucination
        final_score = max(0.0, min(10.0, final_score))
        
        return {
            "FactualConsistency": round(factual_const, 2),
            "EDR": round(edr, 2),
            "Faithfulness": round(faithfulness, 2),
            "HallucinationRate": round(hallucination, 2),
            "Final_Opposition_Score": round(final_score, 2)
        }
    except Exception as e:
        print(f"Opposition Evaluator JSON parse failed: {e}")
        return {}
