from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    # Ollama runs only on your current laptop.
    ollama_base_url: str = "http://127.0.0.1:11434"

    # Exact output from your `ollama list`.
    # SIH requirement: use Local Qwen.
    ollama_model: str = "qwen3:8b"

    # Maximum wait time for local Qwen output.
    llm_timeout_seconds: int = 180

    # Retry count when local Qwen/tool fails.
    max_retries: int = 2

    # Confidence threshold before final response.
    minimum_evidence_confidence: float = 0.50

    # Critical tools cannot run automatically.
    approval_required_tools: list[str] = field(default_factory=lambda: [
        "execute_code_sandbox",
        "write_file",
        "delete_file",
        "send_external_request",
    ])


config = AgentConfig()