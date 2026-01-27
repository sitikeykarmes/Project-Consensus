from app.utils.LLM_agent_client import LLMAgentClient
from dotenv import load_dotenv

load_dotenv()


def test_all_agents():
    print("=" * 60)
    print("Testing Multi-Agent System (ALL GROQ)")
    print("=" * 60 + "\n")

    client = LLMAgentClient()

    test_query = "What is artificial intelligence in one sentence?"

    agents_to_test = {
        "agent1": "GPT-OSS-120B (Groq)",
        "agent2": "Llama 4 scout 17B (Groq)",
        "agent3": "Kimi K2 (Groq)"
    }

    results = {}

    for agent_key, agent_name in agents_to_test.items():
        print(f"\n{'=' * 60}")
        print(f"Testing {agent_name}")
        print(f"{'=' * 60}\n")

        try:
            messages = [
                {"role": "system", "content": f"You are {agent_name}. Answer concisely."},
                {"role": "user", "content": test_query}
            ]

            response = client.get_completion(
                agent_key,
                messages,
                temperature=0.7,
                max_tokens=100
            )

            results[agent_key] = {
                "success": "Error" not in response,
                "response": response
            }

            if "Error" not in response:
                print(f"\n✅ SUCCESS!")
                print(f"Response: {response}\n")
            else:
                print(f"\n❌ FAILED!")
                print(f"Error: {response}\n")

        except Exception as e:
            print(f"\n❌ EXCEPTION!")
            print(f"Error: {str(e)}\n")
            results[agent_key] = {
                "success": False,
                "response": str(e)
            }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60 + "\n")

    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)

    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {total - successful}/{total}\n")

    for agent_key, agent_name in agents_to_test.items():
        status = "✅" if results[agent_key]["success"] else "❌"
        print(f"{status} {agent_name}")

    if successful == total:
        print("\n🎉 All agents working! Ready to run full system.\n")
    elif successful > 0:
        print(f"\n⚠️  {successful} agent(s) working. System will use fallback for failed agents.\n")
    else:
        print("\n❌ All agents failed. Check your API key and internet connection.\n")


if __name__ == "__main__":
    test_all_agents()
