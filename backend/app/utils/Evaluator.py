# backend/app/utils/Evaluator.py
"""
Deterministic Synthesis Evaluator
─────────────────────────────────
Uses purely statistical metrics to evaluate synthesis quality:
  • Faithfulness  : ROUGE recall — is synthesis grounded in agent responses?
  • Relevance     : TF-IDF cosine + query term coverage
  • Conciseness   : compression ratio (synthesis tokens / agent tokens)
  • Coherence     : sentence length, Type-Token Ratio, bigram repetition
  • Agent Coverage: token overlap per agent
"""

import re
import json
import time
import math
from collections import Counter
import os

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
            "composite": round((rel["score"] * 0.5 + coh["score"] * 0.4 + rich * 0.1), 3),
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
    vs_agents = _synthesis_vs_agents(user_query, final_answer, agent_responses)

    d_scores = {
        "faithfulness":   d_faith["score"],
        "relevance":      d_relev["score"],
        "conciseness":    d_conci["score"],
        "coherence":      d_coher["score"],
        "agent_coverage": d_agcov["score"],
    }

    # Format output dictionary so that dependent codes looking for "fused" maps don't break
    metrics = {}
    for k, v in d_scores.items():
        metrics[k] = {"det": round(v, 3), "fused": round(v, 3), "llm": None, "reason": "deterministic only"}

    avg_fused = sum(d_scores.values()) / len(d_scores)

    # ── Verdict ───────────────────────────────────────────────────────────────
    if d_scores["faithfulness"] < 0.30:
        verdict = "FAIL"
    elif d_scores["faithfulness"] < 0.50 or d_scores["relevance"] < 0.35:
        verdict = "WARN"
    else:
        verdict = "PASS"

    elapsed = time.time() - t_start

    result = {
        "metrics":        metrics,
        "det_raw":        d_scores,
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
    print(f"{_BOLD}{_C}  📊 DETERMINISTIC EVALUATION  "
          f"[{r['eval_time_ms']}ms]{_RST}")
    print(f"{_C}{'─' * 66}{_RST}")
    print(f"  {_DIM}Query : {_RST}{_W}{query[:68]}{'…' if len(query)>68 else ''}{_RST}")
    print(f"  {_DIM}Mode  : {_RST}{_B}{mode or 'unknown'}{_RST}")
    print(f"{_C}{'─' * 66}{_RST}")
    print(f"  {_DIM}{'Metric':<16} {'Score':>6}{_RST}")
    print(f"  {_DIM}{'─'*16} {'─'*6}{_RST}")

    for key, label in labels.items():
        v       = m[key]["det"]
        c       = _col(v)
        # scores row
        print(f"  {_W}{label}{_RST} "
              f"{c}{_bar(v)} {v:.2f}{_RST}")

    print(f"{_C}{'─' * 66}{_RST}")
    print(f"  {_W}Avg Score       : {_RST}{_col(r['avg_fused'])}{r['avg_fused']:.3f} / 1.000{_RST}")
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