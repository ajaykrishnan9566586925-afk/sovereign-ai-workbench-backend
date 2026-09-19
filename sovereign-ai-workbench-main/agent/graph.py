from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from agent.nodes import (
    classify_task_node,
    planning_node,
    tool_execution_node,
    evidence_verification_node,
    answer_generation_node,
)


def build_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("classify_task", classify_task_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("evidence_verification", evidence_verification_node)
    workflow.add_node("answer_generation", answer_generation_node)

    workflow.add_edge(START, "classify_task")
    workflow.add_edge("classify_task", "planning")
    workflow.add_edge("planning", "tool_execution")
    workflow.add_edge("tool_execution", "evidence_verification")
    workflow.add_edge("evidence_verification", "answer_generation")
    workflow.add_edge("answer_generation", END)

    return workflow.compile()


agent_graph = build_agent_graph()