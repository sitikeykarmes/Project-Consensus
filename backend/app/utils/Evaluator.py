# backend/app/utils/evaluator.py
"""
Hybrid Synthesis Evaluator
───────────────────────────
Combines two independent evaluation layers:

  Layer 1 — Deterministic (statistical, zero LLM, fully reproducible)
    • Faithfulness  : ROUGE recall — is synthesis grounded in agent responses?
    • Relevance     : TF-IDF cosine + query term coverage
    • Conciseness   : compression ratio (synthesis tokens / agent tokens)
    • Coherence     : sentence length, Type-Token Ratio, bigram repetition
    • Agent Coverage: token overlap per agent

  Layer 2 — LLM Judge (semantic, catches meaning-level issues stats miss)
    • Scores same 5 dimensions 1-5
    • Uses llama-3.3-70b — fast, separate from synthesis model (no self-grading)
    • Given the deterministic scores as anchors to reduce its own hallucination

  Final Score — Weighted Fusion
    • Each metric: 0.6 × deterministic + 0.4 × LLM_judge (normalized)
    • Faithfulness weight flipped: 0.7 deterministic + 0.3 LLM
      (ROUGE is more objective for hallucination than LLM opinion)
    • Conflict detection: if deterministic and LLM disagree by >2 points → FLAG

Dependencies:
    pip install rouge-score scikit-learn
"""

import re
import json
import time
import math
from collections import Counter
from groq import Groq
import os


# ── LLM Judge client ──────────────────────────────────────────────────────────
_groq   = Groq(api_key=os.getenv("GROQ_API_KEY_1"))
_JUDGE  = "llama-3.3-70b-versatile"


# ── Lazy imports ──────────────────────────────────────────────────────────────
def _get_rouge():
    try:
        from rouge_score import rouge_scorer
        return rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    except ImportError:
        return None

def _get_tfidf():
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        return TfidfVectorizer, cosine_similarity
    except ImportError:
        return None, None


# ── ANSI colors ───────────────────────────────────────────────────────────────
_G    = "\033[92m"
_Y    = "\033[93m"
_R    = "\033[91m"
_B    = "\033[94m"
_C    = "\033[96m"
_W    = "\033[97m"
_DIM  = "\033[2m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

STOPWORDS = {
    "a","an","the","is","it","in","on","at","to","of","and","or","but",
    "for","with","this","that","are","was","were","be","been","has","have",
    "had","do","does","did","will","would","could","should","may","might",
    "i","you","he","she","we","they","me","him","her","us","them",
    "my","your","his","its","our","their","what","how","why","when","where",
    "which","who","can","not","no","so","if","as","by","from","about",
}


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — DETERMINISTIC METRICS
# ═══════════════════════════════════════════════════════════════════════════════

def _tokenize(text):
    return re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())

def _meaningful(text):
    return {t for t in _tokenize(text) if t not in STOPWORDS and len(t) > 2}

def _sentences(text):
    return [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]


def _d_faithfulness(synthesis, agents_combined):
    scorer = _get_rouge()
    if scorer:
        s = scorer.score(agents_combined, synthesis)
        r1, r2, rL = s["rouge1"].recall, s["rouge2"].recall, s["rougeL"].recall
        avg = (r1 + r2 + rL) / 3
    else:
        st = set(_tokenize(synthesis))
        at = set(_tokenize(agents_combined))
        avg = r1 = r2 = rL = len(st & at) / max(len(st), 1)
    return {"r1": r1, "r2": r2, "rL": rL, "score": avg}


def _d_relevance(query, synthesis):
    q_terms = _meaningful(query)
    s_tokens = _meaningful(synthesis)
    term_cov = len(q_terms & s_tokens) / max(len(q_terms), 1) if q_terms else 1.0
    missing  = list(q_terms - s_tokens)[:5]

    TfidfVec, cos_sim = _get_tfidf()
    if TfidfVec and len(query.split()) >= 2:
        try:
            v = TfidfVec().fit_transform([query, synthesis])
            cosine = float(cos_sim(v[0], v[1])[0][0])
        except Exception:
            cosine = term_cov
    else:
        cosine = term_cov

    return {"term_coverage": term_cov, "cosine": cosine,
            "score": (term_cov + cosine) / 2, "missing": missing}


def _d_conciseness(synthesis, agents_combined):
    sl = len(_tokenize(synthesis))
    al = len(_tokenize(agents_combined))
    ratio = sl / max(al, 1)
    if 0.10 <= ratio <= 0.50:
        score, note = 1.0, f"Good ({ratio:.0%})"
    elif ratio > 0.60:
        score = max(0.0, 1.0 - (ratio - 0.50) * 2)
        note  = f"Bloated ({ratio:.0%} of agent content)"
    else:
        score = max(0.0, ratio / 0.10)
        note  = f"Too thin ({ratio:.0%} of agent content)"
    return {"ratio": ratio, "score": score, "note": note,
            "synth_tokens": sl, "agent_tokens": al}


def _d_coherence(synthesis):
    sents  = _sentences(synthesis)
    tokens = _tokenize(synthesis)
    avg_sl = (sum(len(_tokenize(s)) for s in sents) / len(sents)) if sents else 0
    sent_score = (1.0 if 10 <= avg_sl <= 30
                  else avg_sl / 10 if avg_sl < 10
                  else max(0.4, 1.0 - (avg_sl - 30) / 50))
    ttr       = len(set(tokens)) / max(len(tokens), 1)
    ttr_score = 1.0 if ttr >= 0.35 else ttr / 0.35
    bigrams   = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
    repeated  = [bg for bg, c in Counter(bigrams).items() if c > 2 and bg not in STOPWORDS]
    rep_score = max(0.0, 1.0 - len(repeated) * 0.1)
    return {"score": (sent_score + ttr_score + rep_score) / 3,
            "avg_sent_len": round(avg_sl, 1), "ttr": round(ttr, 3),
            "repeated": repeated[:3]}


def _d_agent_coverage(synthesis, agent_responses):
    if not agent_responses:
        return {"score": 1.0, "per_agent": []}
    s_tokens = _meaningful(synthesis)
    per_agent = []
    for r in agent_responses:
        a_terms = _meaningful(r.get("content", ""))
        cov = len(a_terms & s_tokens) / max(len(a_terms), 1) if a_terms else 1.0
        per_agent.append({"agent": r.get("agent_name", "?"), "coverage": round(cov, 3)})
    avg = sum(a["coverage"] for a in per_agent) / len(per_agent)
    return {"score": avg, "per_agent": per_agent}


def _synthesis_vs_agents(user_query: str, synthesis: str, agent_responses: list) -> dict:
    """
    Compare synthesis quality vs each individual agent on 3 dimensions.

    Dimensions (all computed against the user query):
      Relevance  — TF-IDF cosine + query term coverage
      Coherence  — sentence structure + TTR + repetition
      Richness   — vocabulary depth (unique meaningful terms / total terms)

    Delta = synthesis_score - agent_score
      + positive  synthesis better than that agent on that dimension
      - negative  agent was actually better on that dimension
    """

    def _score_text(text):
        rel  = _d_relevance(user_query, text)
        coh  = _d_coherence(text)
        toks = _meaningful(text)
        all_t = _tokenize(text)
        rich = len(toks) / max(len(all_t), 1)
        return {
            "relevance": round(rel["score"], 3),
            "coherence": round(coh["score"], 3),
            "richness":  round(rich, 3),
            "composite": round((rel["score"] + coh["score"] + rich) / 3, 3),
        }

    synth_scores = _score_text(synthesis)
    per_agent    = []

    for resp in agent_responses:
        name    = resp.get("agent_name", "Agent")
        content = resp.get("content", "")
        if not content.strip():
            continue
        agent_s = _score_text(content)
        deltas  = {
            dim: round(synth_scores[dim] - agent_s[dim], 3)
            for dim in ["relevance", "coherence", "richness", "composite"]
        }
        per_agent.append({
            "agent":        name,
            "agent_scores": agent_s,
            "deltas":       deltas,
        })

    better_than = sum(1 for a in per_agent if a["deltas"]["composite"] > 0.02)
    worse_than  = sum(1 for a in per_agent if a["deltas"]["composite"] < -0.02)

    return {
        "synthesis_scores": synth_scores,
        "per_agent":        per_agent,
        "better_than":      better_than,
        "worse_than":       worse_than,
        "total_agents":     len(per_agent),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — LLM JUDGE
# ═══════════════════════════════════════════════════════════════════════════════

def _llm_judge(user_query, agents_text, synthesis, mode, d_scores):
    """
    LLM judge is given the deterministic scores as anchors.
    This reduces its tendency to hallucinate scores — it must justify
    any significant deviation from the statistical baseline.
    """

    anchor_block = f"""
Statistical baseline scores (0.0–1.0) for your reference:
  Faithfulness  : {d_scores['faithfulness']:.2f}  (ROUGE recall — grounding in agent content)
  Relevance     : {d_scores['relevance']:.2f}  (TF-IDF cosine + query term coverage)
  Conciseness   : {d_scores['conciseness']:.2f}  (compression ratio)
  Coherence     : {d_scores['coherence']:.2f}  (sentence structure + vocabulary richness)
  Agent Coverage: {d_scores['agent_coverage']:.2f}  (token overlap with all agents)

Your scores should be on a 1–5 scale. Use the baselines above as anchors.
If your semantic judgment strongly disagrees with a baseline, you MUST explain why in the reason field.
"""

    prompt = f"""You are a strict AI evaluation judge. Evaluate this AI synthesis response.

USER QUERY: {user_query}
ORCHESTRATION MODE: {mode or "unknown"}

AGENT RESPONSES (source material the synthesis should be based on):
{agents_text}

FINAL SYNTHESIZED ANSWER:
{synthesis}

{anchor_block}

Score on these 5 dimensions (1–5 each). Focus on SEMANTIC quality the statistics cannot capture:

1. FAITHFULNESS (1–5): Are ALL claims semantically grounded in agent responses?
   Consider meaning, not just word overlap. Watch for subtle fabrications.

2. RELEVANCE (1–5): Does the answer address the actual intent of the query?
   Even if query words appear, did it answer what was really being asked?

3. CONCISENESS (1–5): Is length appropriate for the query complexity and type?
   A greeting answered in 3 paragraphs is wrong even if compression ratio looks ok.

4. COHERENCE (1–5): Does it flow logically? Are there contradictions or non-sequiturs?

5. AGENT_COVERAGE (1–5): Did the synthesis capture the key insight from each agent?
   Not just word overlap — did it use the substance of each agent's contribution?

Respond ONLY with valid JSON (no markdown fences):
{{
  "faithfulness":   {{"score": <1-5>, "reason": "<one sentence>"}},
  "relevance":      {{"score": <1-5>, "reason": "<one sentence>"}},
  "conciseness":    {{"score": <1-5>, "reason": "<one sentence>"}},
  "coherence":      {{"score": <1-5>, "reason": "<one sentence>"}},
  "agent_coverage": {{"score": <1-5>, "reason": "<one sentence>"}}
}}"""

    try:
        resp = _groq.chat.completions.create(
            model=_JUDGE,
            messages=[
                {"role": "system", "content": "You are a strict AI evaluation judge. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=4096,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"{_Y}[Evaluator] LLM judge failed: {e} — using deterministic only{_RST}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# FUSION LAYER — weighted combination + conflict detection
# ═══════════════════════════════════════════════════════════════════════════════

# Weights: how much to trust deterministic vs LLM per metric
# Faithfulness leans more deterministic (ROUGE is objective)
# Conciseness leans more LLM (it understands query type context better)
FUSION_WEIGHTS = {
    "faithfulness":   (0.70, 0.30),
    "relevance":      (0.55, 0.45),
    "conciseness":    (0.45, 0.55),
    "coherence":      (0.50, 0.50),
    "agent_coverage": (0.60, 0.40),
}

CONFLICT_THRESHOLD = 2.0   # flag if LLM and deterministic differ by this many points (on 1-5 scale)


def _fuse(metric, d_score_01, llm_score_15):
    """
    d_score_01  : deterministic score in [0.0, 1.0]
    llm_score_15: LLM score in [1, 5]
    Returns fused score in [0.0, 1.0] and conflict flag
    """
    d_norm   = d_score_01                          # already 0–1
    llm_norm = (llm_score_15 - 1) / 4.0           # normalize 1–5 → 0–1
    w_d, w_l = FUSION_WEIGHTS[metric]
    fused    = w_d * d_norm + w_l * llm_norm

    # Conflict: both on 1–5 scale for comparison
    d_as_15  = d_norm * 4 + 1
    conflict = abs(d_as_15 - llm_score_15) >= CONFLICT_THRESHOLD

    return round(fused, 3), conflict


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_synthesis(
    user_query: str,
    agent_responses: list,
    final_answer: str,
    mode: str = "",
    context_str: str = "",
) -> dict:

    t_start = time.time()
    agents_combined = " ".join(r.get("content", "") for r in agent_responses)
    agents_text     = "\n\n".join(
        f"[{r.get('agent_name','Agent')}]: {r.get('content','')}"
        for r in agent_responses
    )

    # ── Layer 1: Deterministic ────────────────────────────────────────────────
    d_faith = _d_faithfulness(final_answer, agents_combined)
    d_relev = _d_relevance(user_query, final_answer)
    d_conci = _d_conciseness(final_answer, agents_combined)
    d_coher = _d_coherence(final_answer)
    d_agcov = _d_agent_coverage(final_answer, agent_responses)
    vs_agents = _synthesis_vs_agents(user_query, final_answer, agent_responses)  # ← NEW

    d_scores = {
        "faithfulness":   d_faith["score"],
        "relevance":      d_relev["score"],
        "conciseness":    d_conci["score"],
        "coherence":      d_coher["score"],
        "agent_coverage": d_agcov["score"],
    }

    # ── Layer 2: LLM Judge ────────────────────────────────────────────────────
    llm_raw = _llm_judge(user_query, agents_text, final_answer, mode, d_scores)

    # ── Fusion ────────────────────────────────────────────────────────────────
    metrics   = ["faithfulness", "relevance", "conciseness", "coherence", "agent_coverage"]
    fused     = {}
    conflicts = []

    for m in metrics:
        d_val = d_scores[m]
        if llm_raw and m in llm_raw:
            llm_val = llm_raw[m]["score"]
            llm_reason = llm_raw[m]["reason"]
            score, conflict = _fuse(m, d_val, llm_val)
            if conflict:
                conflicts.append({
                    "metric":    m,
                    "det_score": round(d_val * 4 + 1, 1),   # convert to 1–5 for display
                    "llm_score": llm_val,
                    "reason":    llm_reason,
                })
        else:
            score      = d_val          # fall back to deterministic only
            llm_val    = None
            llm_reason = "LLM judge unavailable"

        fused[m] = {
            "det":    round(d_val, 3),
            "llm":    llm_val,
            "fused":  score,
            "reason": llm_reason if llm_raw else "deterministic only",
        }

    # ── Verdict ───────────────────────────────────────────────────────────────
    faith_fused = fused["faithfulness"]["fused"]
    relev_fused = fused["relevance"]["fused"]
    avg_fused   = sum(v["fused"] for v in fused.values()) / len(fused)

    if faith_fused < 0.30:
        verdict = "FAIL"
    elif faith_fused < 0.50 or relev_fused < 0.35 or len(conflicts) >= 2:
        verdict = "WARN"
    else:
        verdict = "PASS"

    elapsed = time.time() - t_start

    result = {
        "metrics":        fused,
        "det_raw":        d_scores,
        "llm_raw":        llm_raw,
        "conflicts":      conflicts,
        "vs_agents":      vs_agents,
        "avg_fused":      round(avg_fused, 3),
        "verdict":        verdict,
        "eval_time_ms":   round(elapsed * 1000, 1),
    }

    _print_scorecard(user_query, mode, result, d_conci)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# TERMINAL PRINTER
# ═══════════════════════════════════════════════════════════════════════════════

def _bar(score_01, width=8):
    filled = max(0, min(width, round(score_01 * width)))
    return "█" * filled + "░" * (width - filled)

def _col(score_01):
    return _G if score_01 >= 0.65 else (_Y if score_01 >= 0.40 else _R)

def _print_scorecard(query, mode, r, d_conci):
    m       = r["metrics"]
    verdict = r["verdict"]
    vc      = _G if verdict == "PASS" else (_Y if verdict == "WARN" else _R)
    vi      = "✅" if verdict == "PASS" else ("⚠️ " if verdict == "WARN" else "❌")

    labels = {
        "faithfulness":   "Faithfulness  ",
        "relevance":      "Relevance     ",
        "conciseness":    "Conciseness   ",
        "coherence":      "Coherence     ",
        "agent_coverage": "Agent Coverage",
    }

    print(f"\n{_BOLD}{_C}{'─' * 66}{_RST}")
    print(f"{_BOLD}{_C}  📊 HYBRID EVALUATION  "
          f"[det+llm fusion | {r['eval_time_ms']}ms]{_RST}")
    print(f"{_C}{'─' * 66}{_RST}")
    print(f"  {_DIM}Query : {_RST}{_W}{query[:68]}{'…' if len(query)>68 else ''}{_RST}")
    print(f"  {_DIM}Mode  : {_RST}{_B}{mode or 'unknown'}{_RST}")
    print(f"{_C}{'─' * 66}{_RST}")
    print(f"  {_DIM}{'Metric':<16} {'Fused':>6}  {'Det':>5}  {'LLM':>4}{_RST}")
    print(f"  {_DIM}{'─'*16} {'─'*6}  {'─'*5}  {'─'*4}{_RST}")

    for key, label in labels.items():
        v       = m[key]
        fused   = v["fused"]
        det     = v["det"]
        llm     = v["llm"]
        reason  = v["reason"]
        llm_str = f"{llm:.1f}" if llm is not None else " n/a"
        c       = _col(fused)
        # scores row
        print(f"  {_W}{label}{_RST} "
              f"{c}{_bar(fused)} {fused:.2f}{_RST}  "
              f"{_DIM}{det:.2f}   {llm_str}{_RST}")
        # reason on its own indented line — no truncation
        print(f"  {_DIM}{'':16}   └─ {reason}{_RST}")

    if r["conflicts"]:
        print(f"\n  {_Y}⚑  CONFLICTS (det vs LLM disagree ≥{CONFLICT_THRESHOLD} pts):{_RST}")
        for cf in r["conflicts"]:
            print(f"  {_Y}  • {cf['metric']}: "
                  f"det={cf['det_score']:.1f}/5  llm={cf['llm_score']}/5{_RST}")
            print(f"  {_Y}    → {cf['reason']}{_RST}")

    print(f"{_C}{'─' * 66}{_RST}")
    print(f"  {_W}Avg Fused Score : {_RST}{_col(r['avg_fused'])}{r['avg_fused']:.3f} / 1.000{_RST}")
    print(f"  {_W}Verdict         : {_RST}{vc}{vi} {verdict}{_RST}")
    print(f"  {_DIM}Conciseness note: {d_conci['note']}{_RST}")
    print(f"{_C}{'─' * 66}{_RST}")

    # ── Synthesis vs Each Agent ───────────────────────────────────────────────
    va = r.get("vs_agents", {})
    if va and va.get("per_agent"):
        ss = va["synthesis_scores"]
        print(f"\n{_BOLD}{_C}  📈 SYNTHESIS vs EACH AGENT{_RST}")
        print(f"{_C}{'─' * 66}{_RST}")
        print(f"  {_DIM}Synthesis baseline → "
              f"Relevance:{ss['relevance']:.2f}  "
              f"Coherence:{ss['coherence']:.2f}  "
              f"Richness:{ss['richness']:.2f}  "
              f"Composite:{ss['composite']:.2f}{_RST}")
        print(f"{_C}{'─' * 66}{_RST}")
        print(f"  {_DIM}{'Agent':<28}  {'Comp':>5}  {'Rel Δ':>6}  {'Coh Δ':>6}  {'Rich Δ':>6}  {'Verdict':>8}{_RST}")
        print(f"  {_DIM}{'─'*28}  {'─'*5}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*8}{_RST}")

        for a in va["per_agent"]:
            name    = a["agent"][:27]
            ag_comp = a["agent_scores"]["composite"]
            d       = a["deltas"]
            comp_d  = d["composite"]

            # color and symbol for each delta
            def _dc(v):
                if v > 0.02:  return f"{_G}+{v:.2f}{_RST}"
                if v < -0.02: return f"{_R}{v:.2f}{_RST}"
                return f"{_DIM}~{abs(v):.2f}{_RST}"

            if comp_d > 0.05:
                verd_str = f"{_G}BETTER ↑{_RST}"
            elif comp_d < -0.05:
                verd_str = f"{_R}WORSE  ↓{_RST}"
            else:
                verd_str = f"{_DIM}SIMILAR ={_RST}"

            print(f"  {_W}{name:<28}{_RST}  "
                  f"{_DIM}{ag_comp:.2f}{_RST}   "
                  f"{_dc(d['relevance'])}    "
                  f"{_dc(d['coherence'])}    "
                  f"{_dc(d['richness'])}   "
                  f"{verd_str}")

        better = va['better_than']
        worse  = va['worse_than']
        total  = va['total_agents']
        equal  = total - better - worse
        print(f"{_C}{'─' * 66}{_RST}")
        print(f"  {_W}Summary :{_RST} "
              f"{_G}Better than {better}/{total} agents{_RST}  "
              f"{_DIM}Similar to {equal}/{total}{_RST}  "
              f"{_R}Worse than {worse}/{total}{_RST}")
        print(f"{_C}{'─' * 66}{_RST}\n")