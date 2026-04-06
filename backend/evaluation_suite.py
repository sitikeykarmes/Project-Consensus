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

# --- TEST QUERIES (Placeholders for 30 Total) ---
QUERIES = {
    "independent": [
        "Compare React, Vue, and Angular for building a large-scale enterprise web application.",
        "What are the trade-offs between microservices and monolithic architecture?",
        "Compare supervised, unsupervised, and reinforcement learning paradigms.",
        "What are the differences between SQL and NoSQL databases?",
        "Compare AWS, Azure, and Google Cloud for a startup deployment.",
        "What are the pros and cons of electric vehicles vs hybrid vs gasoline cars?",
        "Compare Python, Java, and Go for backend development.",
        "What are different investment strategies for a beginner with limited capital?",
        "Compare Agile, Scrum, and Waterfall methodologies for software development.",
        "What are the different approaches to weight loss — diet, exercise, intermittent fasting?",
    ],
    "support": [
        "Explain how the attention mechanism in transformer models works.",
        "How does the human immune system fight a viral infection?",
        "Explain how blockchain achieves decentralization and immutability.",
        "How does garbage collection work in modern programming languages?",
        "Explain the theory of relativity in simple terms.",
        "How does a compiler convert source code to machine code step by step?",
        "Explain how HTTPS and SSL/TLS work to secure internet communication.",
        "How does the water cycle work at a molecular and atmospheric level?",
        "Explain how reinforcement learning trains an agent using rewards and penalties.",
        "How does the stock market determine the price of a share?",
    ],
    "opposition": [
        "Is it true that humans only use 10% of their brains?",
        "Is social media doing more harm than good to society?",
        "Should AI systems be held legally liable for harm caused by their outputs?",
        "Is nuclear energy a safe and viable solution for climate change?",
        "Is it true that eating fat makes you gain weight?",
        "Does screen time actually damage children's cognitive development?",
        "Is cryptocurrency a legitimate financial asset or a speculative bubble?",
        "Should governments mandate algorithmic transparency in AI used for criminal sentencing?",
        "Is remote work more productive than working from office?",
        "Is it ethical to use animal subjects in medical research?",
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
        
        print("\nAll batch testing complete! The results are ready for your project report.")

if __name__ == "__main__":
    main()
