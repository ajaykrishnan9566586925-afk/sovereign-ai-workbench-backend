import os
from fastapi import FastAPI
from pydantic import BaseModel
from app.config import settings
from app.tools import (
    PDFReaderTool,
    OCRTool,
    ExcelAnalyzerTool,
    CalculatorTool,
    FileIOTool,
    WordGeneratorTool,
    PPTGeneratorTool,
    CodeSandboxTool,
    ReportGeneratorTool,
)
os.environ.pop("LANGSMITH_API_KEY", None)
os.environ.pop("LANGSMITH_ENDPOINT", None)
os.environ["LANGSMITH_TRACING"] = "false"
app = FastAPI(title=settings.service_name, version="1.0.0")
TOOLS = {
    "pdf_reader": PDFReaderTool(),
    "ocr_tool": OCRTool(),
    "excel_analyzer": ExcelAnalyzerTool(),
    "calculator": CalculatorTool(),
    "file_io": FileIOTool(),
    "word_generator": WordGeneratorTool(),
    "ppt_generator": PPTGeneratorTool(),
    "code_sandbox": CodeSandboxTool(),
    "report_generator": ReportGeneratorTool(),
}
class ToolRequest(BaseModel):
    tool: str
    arguments: dict = {}
@app.get("/health")
def health():
    return {
        "service": settings.service_name,
        "mode": "local_only",
        "tools": list(TOOLS.keys()),
    }
@app.post("/tool/execute")
def execute_tool(req: ToolRequest):
    if req.tool not in TOOLS:
        return {
            "tool": req.tool,
            "status": "error",
            "result": None,
            "output_file": None,
            "error": f"Unknown tool: {req.tool}",
        }
    tool = TOOLS[req.tool]
    return tool.execute(**req.arguments)
