# backend/app/utils/openrouter_client.py

import os
from openai import OpenAI
from groq import Groq
from typing import Dict, List


class OpenRouterClient:
    def __init__(self):
        # API Keys
        self.openrouter_api_key = os.getenv("OPEN_ROUTER_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY_1")

        # OpenRouter client
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_api_key
        )

        # Groq client
        self.groq_client = Groq(api_key=self.groq_api_key)

        # Agent configuration (model + provider)
        self.models = {
            "agent1": {
                "provider": "groq",
                "model": "openai/gpt-oss-120b"
            },
            "agent2": {
                "provider": "openrouter",
                "model": "meta-llama/llama-3.3-70b-instruct:free"
            },
            "agent3": {
                "provider": "groq",
                "model": "moonshotai/kimi-k2-instruct-0905"
            }
        }

        # OpenRouter headers
        self.extra_headers = {
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Multi-Agent Consensus System"
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
            provider = config["provider"]
            model_name = config["model"]

            print(f"🔄 Requesting {model_key} ({model_name}) via {provider}...")

            # =========================
            # GROQ MODELS (Agent 1 & 3)
            # =========================
            if provider == "groq":
                completion = self.groq_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    top_p=1,
                    stream=False,   # IMPORTANT: disable streaming for compatibility
                )

                content = completion.choices[0].message.content

            # =========================
            # OPENROUTER MODELS (Agent 2)
            # =========================
            elif provider == "openrouter":
                completion = self.openrouter_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_headers=self.extra_headers,
                )

                content = completion.choices[0].message.content

            else:
                raise ValueError(f"Unknown provider: {provider}")

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
