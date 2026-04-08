import os
import json
import time
import csv
from dotenv import load_dotenv

# Load environment variables FIRST before importing backend modules
load_dotenv()

from app.Evaluation.independent_evaluator import evaluate_independent
from app.Evaluation.support_evaluator import evaluate_support
from app.Evaluation.opposition_evaluator import evaluate_opposition
from app.agents.orchestrator import Orchestrator
import app.utils.Evaluator as legacy_eval
import groq

QUERIES = {
    "independent": [
        "Compare quantum computing processing models versus classical computing architecture.",
        "What are the trade-offs between vertical scaling and horizontal scaling in cloud infrastructure?",
        "Compare the strategic differences between chess and Go.",
        "What are the differences between Keynesian and Austrian economic theories?",
        "Compare the long-term impacts of leasing versus buying commercial real estate.",
        "What are the pros and cons of utilizing nuclear fusion compared to advanced geothermal energy?",
        "Compare functional programming in Haskell with object-oriented programming in C++.",
        "What are the different architectural approaches to designing a planetary rover?",
        "Compare cognitive behavioral therapy with psychoanalysis for treating anxiety.",
        "What are the alternative approaches to desalinating ocean water?",
    ],
    "support": [
        "Explain how CRISPR-Cas9 edits genetic sequences at a molecular level.",
        "How do black holes warp spacetime according to general relativity?",
        "Explain how a lithium-ion battery stores and releases electrical energy.",
        "How does a CPU pipeline handle out-of-order execution?",
        "Explain the biological mechanism behind human muscle hypertrophy.",
        "How does the GPS system calculate a precise location on Earth?",
        "Explain how a turbocharger increases engine horsepower.",
        "How does the Federal Reserve use interest rates to control inflation?",
        "Explain the cryptographic principles behind zero-knowledge proofs.",
        "How does a hurricane form and gain energy over warm ocean waters?",
    ],
    "opposition": [
        "Is it true that stretching before a workout prevents injury?",
        "Do artificial sweeteners cause significant disruptions to the human gut microbiome?",
        "Is universal basic income a mathematically sustainable economic policy?",
        "Does violent video game consumption lead to real-world aggression in adolescents?",
        "Is it true that MSG is inherently harmful to human health?",
        "Should human gene editing be permitted for non-therapeutic enhancements?",
        "Is organic farming truly better for the environment than conventional methods?",
        "Should voting be legally mandated for all eligible citizens in a democracy?",
        "Is the deployment of autonomous weapons systems ethically justifiable?",
        "Does the placebo effect have an actual physiological impact on the body?",
    ],
}

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

def main():
    print_banner("INITIALIZING CAPSTONE EVALUATION SUITE")
    orchestrator = Orchestrator()
    reports = []
    
    # Ensure output directory exists
    os.makedirs("eval_results", exist_ok=True)
    
    for mode, queries in QUERIES.items():
        print_banner(f"RUNNING {mode.upper()} MODE")
        
        for idx, query in enumerate(queries):
            print(f"\n[{mode.upper()} Query {idx+1}/{len(queries)}]: {query}")
            
            # Step 1: Run Orchestrator (ALWAYS uses standard API keys for normal platform operation)
            start_time = time.time()
            result = orchestrator.execute_query(user_query=query, mode_override=mode)
            responses = result["agent_responses"]
            synthesis = result["final_answer"]
                    
            # Evaluation Phase
            try:
                
                print("  -> Calculating Legacy Hybrid Metrics (Evaluator.py)...")
                legacy_metrics = legacy_eval.evaluate_synthesis(
                    user_query=query,
                    agent_responses=responses,
                    final_answer=synthesis,
                    mode=mode
                )
                
                generic_fused = {}
                if legacy_metrics and "metrics" in legacy_metrics:
                    generic_fused = legacy_metrics["metrics"]
                
                print("  -> Running Customized Mathematical Judge Analysis...")
                custom_scores = {}
                if mode == "independent":
                    custom_scores = evaluate_independent(query, responses, synthesis, generic_fused)
                elif mode == "support":
                    custom_scores = evaluate_support(query, responses, synthesis, generic_fused)
                elif mode == "opposition":
                    custom_scores = evaluate_opposition(query, responses, synthesis, generic_fused)
                
                eval_time = round(time.time() - start_time, 2)
                print(f"  -> Evaluation Complete in {eval_time}s. Core Score: {custom_scores.get(f'Final_{mode.capitalize()}_Score', 'ERR')}/10.0")
                
                reports.append({
                    "mode": mode,
                    "query": query,
                    "agent_count": len([r for r in responses if 'agent_name' in r]),
                    "synthesis_length": len(synthesis),
                    "agent_responses": "\n\n".join(f"[{r.get('agent_name', 'Agent')}]: {r.get('content', '')}" for r in responses),
                    "synthesis": synthesis,
                    **custom_scores
                })
            except Exception as ex:
                print(f"  [X] Error during evaluation processing: {ex}")

    # Export to CSV
    if reports:
        print_banner("EXPORTING RESULTS")
        csv_file = "eval_results/capstone_metrics_report.csv"
        
        # Get all possible column keys across different modes
        all_keys = ["mode", "query", "agent_count", "synthesis_length", "agent_responses", "synthesis"]
        for r in reports:
            for k in r.keys():
                if k not in all_keys:
                    all_keys.append(k)
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            writer.writerows(reports)
        
        print(f"Successfully generated metrics report at: {csv_file}")
        
        json_file = "eval_results/capstone_metrics_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(reports, f, indent=4)
        print(f"Successfully generated metrics JSON at: {json_file}")
        
        print("\nAll batch testing complete! The results are ready for project report.")

if __name__ == "__main__":
    main()
