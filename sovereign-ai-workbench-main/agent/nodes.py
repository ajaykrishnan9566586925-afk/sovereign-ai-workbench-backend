import json
from typing import Any

from agent.config import config
from agent.llm import get_local_qwen
from agent.logger import make_event, write_local_audit
from agent.tools import LOCAL_TOOLS


def add_event(state: dict, event_type: str, **details) -> tuple[list[dict], dict]:
    event = make_event(event_type, **details)
    write_local_audit(event)

    audit_events = state.get("audit_events", []) + [event]
    return audit_events, event


def classify_task_node(state: dict) -> dict:
    user_input = state.get("user_input", "")
    input_type = state.get("input_type", "text").lower()
    text = user_input.lower()

    # Input type has first priority.
    if input_type in ["image", "scan", "scanned_document"]:
        task_category = "vl_ocr"
        route_reason = "Image/scanned-document input requires local OCR/Qwen-VL route."

    elif input_type in ["excel", "csv", "data"]:
        task_category = "data"
        route_reason = "Structured data input requires local Excel/Pandas route."

    elif input_type in ["code", "python", "java"]:
        task_category = "code"
        route_reason = "Code input requires secure sandbox route with human approval."

    elif any(word in text for word in [
        "excel", "csv", "dataset", "data analysis", "table", "chart"
    ]):
        task_category = "data"
        route_reason = "Keywords indicate data/Excel analysis."

    elif any(word in text for word in [
        "code", "python", "java", "debug", "program", "function"
    ]):
        task_category = "code"
        route_reason = "Keywords indicate code task."

    elif any(word in text for word in [
        "image", "scan", "ocr", "photo", "scanned"
    ]):
        task_category = "vl_ocr"
        route_reason = "Keywords indicate image/OCR task."

    elif any(word in text for word in [
        "report", "proposal", "generate document", "create document"
    ]):
        task_category = "report"
        route_reason = "Keywords indicate report/document generation."

    elif any(word in text for word in [
        "pdf", "manual", "policy", "procedure", "internal document",
        "refinery document", "rag"
    ]):
        task_category = "rag"
        route_reason = "Keywords indicate document retrieval/RAG."

    else:
        task_category = "general"
        route_reason = "General text question; local Qwen direct answer route."

    audit_events, _ = add_event(
        state,
        "task_classified",
        task_category=task_category,
        route_reason=route_reason,
        input_type=input_type,
        selected_model="qwen3:8b",
    )

    progress_event = make_event(
        "progress",
        stage="classification",
        percentage=15,
        message=f"Task classified as {task_category}.",
    )

    return {
        "task_category": task_category,
        "model_to_use": "local_qwen3_8b",
        "route_reason": route_reason,
        "status": "classified",
        "audit_events": audit_events,
        "progress_events": state.get("progress_events", []) + [progress_event],
    }


def planning_node(state: dict) -> dict:
    category = state.get("task_category", "general")
    user_input = state.get("user_input", "")

    tool_calls: list[dict] = []

    if category == "rag":
        tool_calls.append({
            "tool": "local_rag_search",
            "args": {
                "query": user_input,
                "top_k": 3,
            },
        })

    elif category == "vl_ocr":
        file_path = state.get("metadata", {}).get("file_path", "")
        tool_calls.append({
            "tool": "local_image_ocr",
            "args": {
                "image_path": file_path,
            },
        })

    elif category == "data":
        file_path = state.get("metadata", {}).get("file_path", "")
        tool_calls.append({
            "tool": "local_excel_analysis",
            "args": {
                "query": user_input,
                "file_path": file_path,
            },
        })

    elif category == "report":
        tool_calls.append({
            "tool": "local_report_generator",
            "args": {
                "title": "Sovereign AI Workbench Report",
                "content": user_input,
            },
        })

    elif category == "code":
        tool_calls.append({
            "tool": "execute_code_sandbox",
            "args": {
                "code": user_input,
            },
        })

    plan = [
        "Receive and validate the user request",
        f"Route the request to the '{category}' workflow",
        "Execute approved local tools only",
        "Collect and verify local evidence",
        "Generate a local Qwen response",
        "Return structured JSON and audit events",
    ]

    audit_events, _ = add_event(
        state,
        "plan_created",
        task_category=category,
        tool_call_count=len(tool_calls),
    )

    progress_event = make_event(
        "progress",
        stage="planning",
        percentage=30,
        message="Multi-step local agent plan created.",
    )

    return {
        "plan": plan,
        "tool_calls": tool_calls,
        "current_step": 1,
        "status": "planned",
        "audit_events": audit_events,
        "progress_events": state.get("progress_events", []) + [progress_event],
    }


def tool_execution_node(state: dict) -> dict:
    tool_calls = state.get("tool_calls", [])
    results = []
    audit_events = state.get("audit_events", [])
    needs_human_approval = False
    approval_reason = None

    for call in tool_calls:
        tool_name = call.get("tool", "")
        args = call.get("args", {})

        if tool_name not in LOCAL_TOOLS:
            event = make_event(
                "tool_failed",
                tool=tool_name,
                reason="Tool not found.",
            )
            write_local_audit(event)

            audit_events.append(event)
            results.append({
                "tool": tool_name,
                "status": "failed",
                "error": "Tool not found.",
            })
            continue

        if tool_name in config.approval_required_tools:
            needs_human_approval = True
            approval_reason = (
                f"Critical operation requested through '{tool_name}'. "
                "Human approval is mandatory before execution."
            )

            event = make_event(
                "human_approval_required",
                tool=tool_name,
                reason=approval_reason,
            )
            write_local_audit(event)

            audit_events.append(event)
            results.append({
                "tool": tool_name,
                "status": "pending_human_approval",
                "args": args,
                "message": approval_reason,
            })
            continue

        try:
            tool_result = LOCAL_TOOLS[tool_name](**args)

            event = make_event(
                "tool_executed",
                tool=tool_name,
                status=tool_result.get("status", "success"),
            )
            write_local_audit(event)

            audit_events.append(event)
            results.append({
                "tool": tool_name,
                "status": tool_result.get("status", "success"),
                "args": args,
                "result": tool_result.get("result", {}),
            })

        except Exception as error:
            event = make_event(
                "tool_failed",
                tool=tool_name,
                reason=str(error),
            )
            write_local_audit(event)

            audit_events.append(event)
            results.append({
                "tool": tool_name,
                "status": "failed",
                "args": args,
                "error": str(error),
            })

    progress_event = make_event(
        "progress",
        stage="tool_execution",
        percentage=55,
        message="Local tool execution stage completed.",
    )

    return {
        "tool_results": results,
        "tool_execution_status": (
            "pending_human_approval"
            if needs_human_approval
            else "completed"
        ),
        "needs_human_approval": needs_human_approval,
        "approval_reason": approval_reason,
        "status": (
            "pending_human_approval"
            if needs_human_approval
            else "tools_completed"
        ),
        "audit_events": audit_events,
        "progress_events": state.get("progress_events", []) + [progress_event],
    }


def evidence_verification_node(state: dict) -> dict:
    tool_results = state.get("tool_results", [])
    evidence_items = []
    confidence_values = []

    for tool_result in tool_results:
        if tool_result.get("status") != "success":
            continue

        tool_name = tool_result.get("tool", "")
        result = tool_result.get("result", {})

        if tool_name == "local_rag_search" and isinstance(result, list):
            for item in result:
                evidence_items.append({
                    "source": item.get("source_name", "Local RAG"),
                    "source_id": item.get("source_id", "unknown"),
                    "snippet": item.get("snippet", ""),
                    "confidence": item.get("confidence", 0.50),
                })
                confidence_values.append(item.get("confidence", 0.50))

        else:
            confidence = result.get("confidence", 0.60)

            evidence_items.append({
                "source": f"local_tool:{tool_name}",
                "source_id": tool_name,
                "snippet": str(result)[:600],
                "confidence": confidence,
            })
            confidence_values.append(confidence)

    category = state.get("task_category", "general")

    if category == "general" and not evidence_items:
        evidence_confidence = 0.50
        evidence_verified = True

    elif evidence_items:
        evidence_confidence = round(
            sum(confidence_values) / len(confidence_values),
            2,
        )
        evidence_verified = (
            evidence_confidence >= config.minimum_evidence_confidence
        )

    else:
        evidence_confidence = 0.0
        evidence_verified = False

    event = make_event(
        "evidence_verified",
        evidence_count=len(evidence_items),
        confidence=evidence_confidence,
        verified=evidence_verified,
    )
    write_local_audit(event)

    progress_event = make_event(
        "progress",
        stage="evidence_verification",
        percentage=75,
        message=(
            f"Evidence verification completed. "
            f"Confidence: {evidence_confidence}"
        ),
    )

    return {
        "evidence_items": evidence_items,
        "evidence_confidence": evidence_confidence,
        "evidence_verified": evidence_verified,
        "status": "evidence_verified",
        "audit_events": state.get("audit_events", []) + [event],
        "progress_events": state.get("progress_events", []) + [progress_event],
    }


def answer_generation_node(state: dict) -> dict:
    category = state.get("task_category", "general")
    user_input = state.get("user_input", "")
    evidence_items = state.get("evidence_items", [])
    tool_results = state.get("tool_results", [])
    needs_approval = state.get("needs_human_approval", False)
    evidence_verified = state.get("evidence_verified", False)
    confidence = state.get("evidence_confidence", 0.0)

    if needs_approval:
        final_answer = (
            "Your request includes a critical operation. "
            "The operation was not executed automatically because "
            "human approval is required."
        )

        structured_output = {
            "status": "pending_human_approval",
            "task_category": category,
            "model": "local_qwen3_8b",
            "summary": "Critical tool action is waiting for human approval.",
            "key_findings": [],
            "source_references": evidence_items,
            "evidence_confidence": confidence,
            "evidence_verified": False,
            "approval_required": True,
            "approval_reason": state.get("approval_reason"),
            "tool_execution_status": state.get("tool_execution_status"),
            "suggested_actions": [
                "Review the requested critical operation.",
                "Approve or reject through the backend approval endpoint.",
                "Use a Docker/restricted local sandbox before code execution.",
            ],
        }

    else:
        system_prompt = """
You are the Local Qwen reasoning and answer agent in a Sovereign AI Workbench.

Strict rules:
1. You are operating locally through Ollama.
2. Do not claim to use cloud services or external APIs.
3. Use only the provided local tool results and evidence.
4. If evidence is placeholder/incomplete, clearly state that.
5. Do not invent internal refinery procedures, document facts, or source details.
6. Give a professional, useful and concise answer.
"""

        prompt = f"""
User request:
{user_input}

Task category:
{category}

Local tool results:
{json.dumps(tool_results, ensure_ascii=False, default=str)}

Local evidence:
{json.dumps(evidence_items, ensure_ascii=False, default=str)}

Evidence verified:
{evidence_verified}

Evidence confidence:
{confidence}

Write the final answer now.
"""

        try:
            final_answer = get_local_qwen().chat(
                user_prompt=prompt,
                system_prompt=system_prompt,
            )

            status = "completed"

        except Exception as error:
            final_answer = (
                "The agent could not generate a response from Local Qwen. "
                f"Error: {str(error)}"
            )

            status = "failed"

        structured_output = {
            "status": status,
            "task_category": category,
            "model": "local_qwen3_8b",
            "summary": final_answer[:500],
            "key_findings": [
                item.get("snippet", "")[:300]
                for item in evidence_items
            ],
            "source_references": evidence_items,
            "evidence_confidence": confidence,
            "evidence_verified": evidence_verified,
            "approval_required": False,
            "approval_reason": None,
            "tool_execution_status": state.get("tool_execution_status"),
            "suggested_actions": [
                "Review the local source references.",
                "Replace placeholder local tools with production RAG/OCR/Data services.",
            ],
        }

    event = make_event(
        "answer_generated",
        task_category=category,
        model="qwen3:8b",
        evidence_confidence=confidence,
        approval_required=needs_approval,
    )
    write_local_audit(event)

    progress_event = make_event(
        "progress",
        stage="completed",
        percentage=100,
        message="Agent workflow completed.",
    )

    return {
        "final_answer": final_answer,
        "structured_output": structured_output,
        "status": structured_output["status"],
        "audit_events": state.get("audit_events", []) + [event],
        "progress_events": state.get("progress_events", []) + [progress_event],
    }


def failure_recovery_node(state: dict) -> dict:
    retry_count = state.get("retry_count", 0)
    error_message = state.get("error_message", "Unknown failure.")

    if retry_count >= config.max_retries:
        final_answer = (
            "Agent execution failed after reaching the retry limit. "
            f"Error: {error_message}"
        )

        structured_output = {
            "status": "failed",
            "task_category": state.get("task_category", "unknown"),
            "model": "local_qwen3_8b",
            "summary": final_answer,
            "key_findings": [],
            "source_references": [],
            "evidence_confidence": 0.0,
            "evidence_verified": False,
            "approval_required": False,
            "approval_reason": None,
            "tool_execution_status": "failed",
            "suggested_actions": [
                "Check local audit logs.",
                "Verify Ollama service is running.",
                "Retry the request.",
            ],
        }

        event = make_event(
            "failure_recovery_exhausted",
            retry_count=retry_count,
            error=error_message,
        )
        write_local_audit(event)

        return {
            "final_answer": final_answer,
            "structured_output": structured_output,
            "status": "failed",
            "audit_events": state.get("audit_events", []) + [event],
        }

    event = make_event(
        "retry_scheduled",
        retry_count=retry_count + 1,
        error=error_message,
    )
    write_local_audit(event)

    return {
        "retry_count": retry_count + 1,
        "audit_events": state.get("audit_events", []) + [event],
    }