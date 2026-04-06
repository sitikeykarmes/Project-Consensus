# backend/app/Evaluation/support_evaluator.py
import json
import os

def evaluate_support(user_query: str, agent_responses: list, final_answer: str, generic_metrics: dict) -> dict:
    """
    Support Mode — Primary Strength: Depth and Sequential Enrichment
    Calculates: Support Score = 0.40×ICS + 0.35×ExplanationCompleteness + 0.25×Coherence − RedundancyPenalty
    """
    import groq
    client = groq.Groq(api_key=os.getenv("consensus_test_1"))
    agents_text = "\n\n".join(f"[{r.get('agent_name', 'Agent')}]: {r.get('content', '')}" for r in agent_responses)

    prompt = f"""You are a strict AI evaluation judge scoring a Support/Tutorial Mode synthesis.
    
USER QUERY: {user_query}

AGENT RESPONSES (These were generated sequentially to build on each other):
{agents_text}

FINAL SYNTHESIZED ANSWER:
{final_answer}

Score the following metrics strictly on a scale of 0.0 to 10.0:
1. "ICS" (Incremental Coverage Score): How well did the synthesis layer the sequential steps built by the agents into a cohesive whole? (0.0 to 10.0)
2. "ExplanationCompleteness": Is the final answer a complete, unbroken tutorial or deep dive that successfully bridges any gaps? (0.0 to 10.0)
3. "RedundancyPenalty": Did the synthesis repetitively state the exact same facts redundantly because multiple agents said them? (Penalty: 0.0 to 2.0. 0.0 means perfect flow, 2.0 means highly redundant).

Respond exactly with a valid JSON object matching this schema (replace the example values with your actual calculated scores):
{{
  "ICS": <Float between 0.0 and 10.0>,
  "ExplanationCompleteness": <Float between 0.0 and 10.0>,
  "RedundancyPenalty": <Float between 0.0 and 2.0>
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
                        print(f"Support Evaluator failed on 3rd fallback key: {e3}")
                        return {}
                else:
                    return {}
            except Exception as e2:
                print(f"Support Evaluator failed on 2nd fallback key: {e2}")
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
        
        # Generic metric 'Coherence' comes from the 0-1 scaled composite
        coherence = generic_metrics.get("coherence", {}).get("fused", 0.8) * 10.0
        
        ics = data.get("ICS", 5.0)
        completeness = data.get("ExplanationCompleteness", 5.0)
        penalty = data.get("RedundancyPenalty", 0.0)
        
        final_score = (0.40 * ics) + (0.35 * completeness) + (0.25 * coherence) - penalty
        final_score = max(0.0, min(10.0, final_score))
        
        return {
            "ICS": round(ics, 2),
            "ExplanationCompleteness": round(completeness, 2),
            "Coherence": round(coherence, 2),
            "RedundancyPenalty": round(penalty, 2),
            "Final_Support_Score": round(final_score, 2)
        }
    except Exception as e:
        print(f"Support Evaluator JSON parse failed: {e}")
        return {}
