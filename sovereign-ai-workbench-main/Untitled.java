import os

from fastapi import FastAPI

from api.schemas import AgentRequest, AgentResponse
from agent.graph import agent_graph


# Force LangSmith tracing OFF every time this API starts.
os.environ.pop("LANGSMITH_API_KEY", None)
os.environ.pop("LANGSMITH_ENDPOINT", None)
os.environ["LANGSMITH_TRACING"] = "false"


app = FastAPI(title="Sovereign AI Workbench - Local Qwen Agent")


@app.get("/health")
def health():
    return {
        "status": "running",
        "model": "qwen3:8b",
        "mode": "local_only",
        "langsmith_tracing": "false",
    }


@app.post("/agent/invoke", response_model=AgentResponse)
def invoke_agent(request: AgentRequest):
    result = agent_graph.invoke({
        "user_input": request.user_input,
        "audit_events": [],
    })

    return AgentResponse(
        success=True,
        task_type=result["task_type"],
        final_answer=result["final_answer"],
        evidence=result["evidence"],
        audit_events=result["audit_events"],
    )