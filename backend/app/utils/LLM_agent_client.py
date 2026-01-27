# backend/app/utils/LLM_agent_client.py

import os
from groq import Groq
from typing import Dict, List


class LLMAgentClient:
    def __init__(self):
        # Groq API Key
        self.groq_api_key = os.getenv("GROQ_API_KEY_1")

        # Groq client
        self.groq_client = Groq(api_key=self.groq_api_key)

        # Agent configuration (ALL from GROQ)
        self.models = {
            "agent1": {
                "provider": "groq",
                "model": "openai/gpt-oss-120b"
            },
            "agent2": {
                "provider": "groq",
                "model": "meta-llama/llama-4-scout-17b-16e-instruct"
            },
            "agent3": {
                "provider": "groq",
                "model": "moonshotai/kimi-k2-instruct-0905"
            }
        }

    def get_completion(
        self,
        model_key: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        try:
            config = self.models[model_key]
            model_name = config["model"]

            print(f"🔄 Requesting {model_key} ({model_name}) via Groq...")

            completion = self.groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
                top_p=1,
                stream=False,  # keep false for compatibility
            )

            content = completion.choices[0].message.content

            print(f"✅ {model_key} completed successfully")
            return content

        except Exception as e:
            error_msg = f"Error with {model_key} ({self.models.get(model_key, {}).get('model', 'unknown')}): {str(e)}"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"

    def test_connection(self) -> bool:
        try:
            test_messages = [{"role": "user", "content": "Hi"}]
            result = self.get_completion("agent1", test_messages, max_tokens=10)
            return "Error" not in result
        except:
            return False
