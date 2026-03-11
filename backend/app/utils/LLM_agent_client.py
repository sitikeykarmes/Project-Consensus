# backend/app/utils/LLM_agent_client.py

import os
from groq import Groq
from typing import Dict, List


class LLMAgentClient:
    def __init__(self):
        # -----------------------------
        # Load Groq API Key
        # -----------------------------
        self.groq_api_key = os.getenv("GROQ_API_KEY_1")

        if not self.groq_api_key:
            raise ValueError("❌ GROQ_API_KEY_1 is missing in environment variables!")

        # -----------------------------
        # Initialize Groq Client
        # -----------------------------
        self.groq_client = Groq(api_key=self.groq_api_key)

        # -----------------------------
        # Agent Configuration (All Groq)
        # -----------------------------
        self.models = {
            "agent1": {
                "provider": "groq",
                "model": "openai/gpt-oss-120b",
            },
            "agent2": {
                "provider": "groq",
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            },
            "agent3": {
                "provider": "groq",
                "model": "moonshotai/kimi-k2-instruct-0905",
            },
            "agent4": {
                "provider": "groq",
                "model": "qwen/qwen3-32b",
                "streaming": True,          # agent4 uses streaming
                "temperature": 0.6,
                "top_p": 0.95,
                "reasoning_effort": "default",
            },
        }

    # -------------------------------------------------
    # Main Completion Function (Non-Streaming Agents)
    # -------------------------------------------------
    def get_completion(
        self,
        model_key: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str:
        """
        Calls Groq chat completion safely.
        Routes agent4 to the streaming handler automatically.

        Features:
        - Retries up to 4 times
        - Fixes blank model replies
        - Token boost on retries
        - Clean + scalable retry logic
        """

        # -----------------------------
        # Validate model key
        # -----------------------------
        if model_key not in self.models:
            return f"Error: Unknown model key '{model_key}'"

        # -----------------------------
        # Route agent4 to streaming handler
        # -----------------------------
        if self.models[model_key].get("streaming"):
            return self.get_streaming_completion(model_key, messages, max_tokens)

        model_name = self.models[model_key]["model"]

        # -----------------------------
        # Internal helper for Groq call
        # -----------------------------
        def _call_model(token_boost: int = 0):
            return self.groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens + token_boost,
                top_p=1,
                stream=False,
            )

        try:
            print(f"🔄 Requesting {model_key} ({model_name}) via Groq...")

            # -----------------------------------------
            # Retry Attempts (4 total)
            # -----------------------------------------
            token_boosts = [400, 500, 600, 700]

            for attempt, boost in enumerate(token_boosts, start=1):

                completion = _call_model(token_boost=boost)
                content = completion.choices[0].message.content

                # ✅ If valid response, return immediately
                if content and content.strip():
                    print(f"✅ {model_key} succeeded on attempt {attempt}")
                    return content.strip()

                # ⚠️ Blank response → retry
                print(
                    f"⚠️ {model_key} returned blank output on attempt {attempt}. Retrying..."
                )

            # -----------------------------------------
            # Final fallback if all attempts fail
            # -----------------------------------------
            print(f"❌ {model_key} failed after 4 attempts (blank output).")
            return "⚠️ Agent did not respond properly after 4 attempts. Please try again."

        except Exception as e:
            error_msg = f"Error with {model_key} ({model_name}): {str(e)}"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"

    # -------------------------------------------------
    # Streaming Completion Function (agent4 / Qwen)
    # -------------------------------------------------
    def get_streaming_completion(
        self,
        model_key: str,
        messages: List[Dict],
        max_tokens: int = 4096,
    ) -> str:
        """
        Handles streaming completions for agent4 (qwen/qwen3-32b).
        Collects all streamed chunks and returns the full response as a string.
        """

        model_config = self.models[model_key]
        model_name = model_config["model"]

        try:
            print(f"🔄 Requesting {model_key} ({model_name}) via Groq [streaming]...")

            completion = self.groq_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=model_config.get("temperature", 0.6),
                max_completion_tokens=max_tokens,
                top_p=model_config.get("top_p", 0.95),
                reasoning_effort=model_config.get("reasoning_effort", "default"),
                stream=True,
                stop=None,
            )

            # Collect all streamed chunks into a single string
            full_response = ""
            for chunk in completion:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response += delta

            # Strip Qwen's internal <think>...</think> reasoning block
            import re
            full_response = re.sub(r"<think>.*?</think>", "", full_response, flags=re.DOTALL).strip()

            if full_response:
                print(f"✅ {model_key} streaming completed successfully.")
                return full_response

            print(f"❌ {model_key} returned blank streaming output.")
            return "⚠️ Agent did not respond properly. Please try again."

        except Exception as e:
            error_msg = f"Error with {model_key} ({model_name}): {str(e)}"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"

    # -------------------------------------------------
    # Quick Connection Test
    # -------------------------------------------------
    def test_connection(self) -> bool:
        """
        Quick check if Groq + agent1 works properly.
        """

        try:
            test_messages = [{"role": "user", "content": "Hello"}]

            result = self.get_completion(
                model_key="agent1",
                messages=test_messages,
                max_tokens=20,
            )

            return "Error" not in result

        except:
            return False