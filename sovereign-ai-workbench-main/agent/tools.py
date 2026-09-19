from datetime import datetime


def local_rag_search(query: str, top_k: int = 3) -> dict:
    """
    SAFE PLACEHOLDER.

    Later replace this with actual local RAG:
    PDF/DOCX -> chunks -> local embeddings -> FAISS/Chroma/Qdrant -> sources.
    """

    sources = [
        {
            "source_id": "local_rag_placeholder_001",
            "source_name": "Internal local knowledge base placeholder",
            "snippet": (
                f"Placeholder local RAG result for query: {query}. "
                "Replace this function with real local document retrieval."
            ),
            "confidence": 0.65,
        }
    ][:top_k]

    return {
        "status": "success",
        "tool": "local_rag_search",
        "result": sources,
    }


def local_image_ocr(image_path: str = "") -> dict:
    """
    SAFE PLACEHOLDER for Qwen-VL + OCR pipeline.

    Later replace using Qwen-VL through Ollama / local runtime and OCR.
    """

    return {
        "status": "success",
        "tool": "local_image_ocr",
        "result": {
            "image_path": image_path,
            "extracted_text": (
                "Placeholder OCR result. Connect Local Qwen-VL and OCR here."
            ),
            "confidence": 0.55,
        },
    }


def local_excel_analysis(query: str, file_path: str = "") -> dict:
    """
    SAFE PLACEHOLDER for Pandas / Excel analysis.

    Later use pandas.read_excel or pandas.read_csv.
    """

    return {
        "status": "success",
        "tool": "local_excel_analysis",
        "result": {
            "file_path": file_path,
            "query": query,
            "summary": (
                "Placeholder data analysis. "
                "Connect pandas and local Excel/CSV files here."
            ),
            "confidence": 0.60,
        },
    }


def local_report_generator(title: str, content: str) -> dict:
    """
    SAFE PLACEHOLDER for local DOCX/PDF report generation.

    Later use python-docx or reportlab.
    """

    return {
        "status": "success",
        "tool": "local_report_generator",
        "result": {
            "title": title,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "message": (
                "Placeholder report created logically. "
                "Connect python-docx/reportlab for actual file generation."
            ),
            "content_preview": content[:300],
            "confidence": 0.60,
        },
    }


def execute_code_sandbox(code: str) -> dict:
    """
    BLOCKED BY DESIGN.

    Never use exec(code) directly.
    Code requests will require a human approval state.
    Later use Docker/restricted subprocess sandbox.
    """

    return {
        "status": "blocked",
        "tool": "execute_code_sandbox",
        "result": {
            "message": (
                "Code was not executed. "
                "Human approval and a secure local sandbox are required."
            ),
            "code_length": len(code),
        },
    }


LOCAL_TOOLS = {
    "local_rag_search": local_rag_search,
    "local_image_ocr": local_image_ocr,
    "local_excel_analysis": local_excel_analysis,
    "local_report_generator": local_report_generator,
    "execute_code_sandbox": execute_code_sandbox,
}