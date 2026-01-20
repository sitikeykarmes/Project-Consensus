from app.agents.orchestrator import Orchestrator
from dotenv import load_dotenv
import sys

load_dotenv()

def run_interactive_test():
    print("="*60)
    print("Project Consensus: Interactive Terminal Test")
    print("Type 'exit' or 'quit' to stop.")
    print("="*60 + "\n")

    orchestrator = Orchestrator()

    while True:
        try:
            # Step 1: Get user input from terminal
            query = input("\nUser Query > ").strip()

            # Step 2: Check for exit command
            if query.lower() in ['exit', 'quit']:
                print("\nExiting test. Goodbye!")
                break
            
            if not query:
                continue

            print(f"\nProcessing query...")
            
            # Step 3: Execute orchestration logic
            result = orchestrator.execute_query(query)

            # Step 4: Display Results
            print(f"\n{'='*60}")
            print(f"MODE USED: {result['mode_used'].upper()}")
            print(f"{'='*60}\n")

            # Show individual agent contributions
            for response in result['agent_responses']:
                print(f"{'-'*40}")
                print(f"[{response['agent_name']}]")
                print(f"{'-'*40}")
                print(response['content'])
                print()

            # Show final synthesis
            print(f"{'='*60}")
            print("FINAL CONSENSUS:")
            print(f"{'='*60}")
            print(result['final_answer'])
            print(f"{'='*60}\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    run_interactive_test()