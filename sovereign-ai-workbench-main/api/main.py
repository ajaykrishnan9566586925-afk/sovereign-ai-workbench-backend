from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.document_intelligence import answer_question, as_jsonable, extract_document

os.environ.pop("LANGSMITH_API_KEY", None)
os.environ.pop("LANGSMITH_ENDPOINT", None)
os.environ["LANGSMITH_TRACING"] = "false"

ROOT = Path(__file__).resolve().parent.parent
STATIC_FILES = {"index.html", "app.js", "styles.css"}

app = FastAPI(title="Sovereign AI Workbench", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=ROOT), name="static")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "local_only", "document_qa": "ready"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "index.html")


@app.get("/{asset_name}")
def frontend_asset(asset_name: str):
    if asset_name in STATIC_FILES:
        return FileResponse(ROOT / asset_name)
    return {"detail": "Not found"}


@app.post("/api/agent/tasks")
@app.post("/agent/tasks")
async def run_task(
    task: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    access_classification: str = Form("INTERNAL"),
):
    request_id = str(uuid4())
    documents = []
    errors = []

    with tempfile.TemporaryDirectory(prefix="sovereign-workbench-") as temp_dir:
        temp_root = Path(temp_dir)
        for upload in files:
            if not upload.filename:
                continue
            try:
                safe_name = Path(upload.filename).name
                target = temp_root / safe_name
                target.write_bytes(await upload.read())
                documents.append(extract_document(target, safe_name))
            except Exception as exc:
                errors.append({"file": upload.filename, "error": str(exc)})

        answer, retrieved = answer_question(task, documents) if documents else (
            "No files were uploaded. Please upload one or more documents before asking a document question.", []
        )

        evidence = [
            {
                "file": item["file"],
                "detail": f"{item['detail']} · relevance {item['score']:.0%}",
                "content": item["content"],
                "page": item.get("page"),
            }
            for item in retrieved
        ]
        if not evidence and documents:
            evidence = [{"file": document.filename, "detail": f"{document.extension.upper()} · indexed", "content": document.text[:500]} for document in documents]

        status = "completed" if documents and not errors else ("completed_with_warnings" if documents else "failed")
        return {
            "success": bool(documents),
            "request_id": request_id,
            "status": status,
            "answer": answer.replace("\n", "<br>"),
            "final_answer": answer,
            "task_category": "document_question_answering" if documents else "document_upload_required",
            "model": "local_extractive_retrieval",
            "evidence": evidence,
            "evidence_items": evidence,
            "documents": as_jsonable(documents),
            "errors": errors,
            "approval_required": False,
            "progress_events": [
                {"event": "files_received", "count": len(files)},
                {"event": "documents_extracted", "count": len(documents)},
                {"event": "retrieval_completed", "count": len(retrieved)},
            ],
        }


@app.post("/api/documents/ingest")
async def ingest_documents(files: list[UploadFile] = File(default=[])):
    results = []
    with tempfile.TemporaryDirectory(prefix="sovereign-ingest-") as temp_dir:
        root = Path(temp_dir)
        for upload in files:
            if not upload.filename:
                continue
            try:
                name = Path(upload.filename).name
                path = root / name
                path.write_bytes(await upload.read())
                document = extract_document(path, name)
                results.append({"success": True, "document": as_jsonable([document])[0]})
            except Exception as exc:
                results.append({"success": False, "document_name": upload.filename, "error": str(exc)})
    return {"success": all(item["success"] for item in results) if results else False, "results": results}
