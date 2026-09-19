import os
import httpx

from agent.config import config


# ----------------------------------------------------------------
# Sovereign mode:
# LangSmith cloud tracing must never receive confidential data.
# ----------------------------------------------------------------
os.environ.pop("LANGSMITH_API_KEY", None)
os.environ.pop("LANGSMITH_ENDPOINT", None)
os.environ["LANGSMITH_TRACING"] = "false"


class LocalQwenClient:
    def __init__(self) -> None:
        self.base_url = config.ollama_base_url.rstrip("/")
        self.model = config.ollama_model

    def chat(self, user_prompt: str, system_prompt: str = "") -> str:
        messages = [
            {
                "role": "system",
                "content": "/no_think",
            }
        ]

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })

        messages.append({
            "role": "user",
            "content": user_prompt,
        })

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        try:
            with httpx.Client(timeout=config.llm_timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

            response.raise_for_status()

            data = response.json()

            return data.get("message", {}).get(
                "content",
                "",
            ).strip()

        except httpx.ConnectError as error:
            raise RuntimeError(
                "Cannot connect to local Ollama. Ensure Ollama is running "
                "at http://127.0.0.1:11434."
            ) from error

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                f"Local Ollama returned an error: {error.response.text}"
            ) from error


def get_local_qwen() -> LocalQwenClient:
    return LocalQwenClient()