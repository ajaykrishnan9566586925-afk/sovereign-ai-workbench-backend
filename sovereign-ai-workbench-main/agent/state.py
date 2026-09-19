from typing import TypedDict, Optional, Any


class AgentState(TypedDict, total=False):
    # Request identity and input
    request_id: str
    user_input: str
    input_type: str
    metadata: dict[str, Any]

    # Classification and routing
    task_category: str
    model_to_use: str
    route_reason: str

    # Agent plan
    plan: list[str]
    current_step: int

    # Tool layer
    tool_calls: list[dict]
    tool_results: list[dict]
    tool_execution_status: str

    # Human approval
    needs_human_approval: bool
    approval_reason: Optional[str]
    human_approval_status: Optional[str]

    # Evidence layer
    evidence_items: list[dict]
    evidence_confidence: float
    evidence_verified: bool

    # Agent status/progress
    progress_events: list[dict]
    audit_events: list[dict]

    # Retry and errors
    retry_count: int
    error_message: Optional[str]

    # Final structured API output
    final_answer: Optional[str]
    structured_output: Optional[dict]
    status: str