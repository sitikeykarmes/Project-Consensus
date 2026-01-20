from app.agents.orchestrator import Orchestrator
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("Testing Project Consensus with Groq")
print("="*60 + "\n")

orchestrator = Orchestrator()

# Test query
query = "Which government party is better, BJP or Congress?"
print(f"Query: {query}\n")

result = orchestrator.execute_query(query)

print(f"\n{'='*60}")
print(f"Mode Used: {result['mode_used'].upper()}")
print(f"{'='*60}\n")

for response in result['agent_responses']:
    print(f"{'='*60}")
    print(f"[{response['agent_name']}]")
    print(f"{'='*60}")
    print(response['content'])
    print()

print(f"\n{'='*60}")
print("FINAL CONSENSUS:")
print(f"{'='*60}")
print(result['final_answer'])
print(f"{'='*60}")
