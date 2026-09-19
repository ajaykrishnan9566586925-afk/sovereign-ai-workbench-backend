import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import IngestResponse, SearchRequest, SearchResponse
from app.service import LocalRAGService


# Explicit local-only privacy safety.
os.environ.pop("LANGSMITH_API_KEY", None)
os.environ.pop("LANGSMITH_ENDPOINT", None)
os.environ["LANGSMITH_TRACING"] = "false"


app = FastAPI(
    title="Local Document Intelligence and RAG Service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = LocalRAGService()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "local_only",
        "vector_database": "Qdrant local persistent storage",
        "embedding_model": "BAAI/bge-m3",
        "external_embedding_api": False,
        "cloud_rag": False,
    }


@app.post("/documents/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    access_classification: str = Form("INTERNAL"),
    metadata_json: str = Form("{}"),
):
    temp_path = None

    try:
        try:
            import json
            metadata = json.loads(metadata_json)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="metadata_json must be valid JSON.",
            )

        suffix = Path(file.filename or "uploaded_file").suffix

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temporary:
            temp_path = Path(temporary.name)
            shutil.copyfileobj(file.file, temporary)

        result = rag_service.ingest(
            temp_file_path=temp_path,
            original_filename=file.filename or "uploaded_file",
            access_classification=access_classification,
            metadata=metadata,
        )

        return result

    except HTTPException:
        raise

    except Exception as error:
        return IngestResponse(
            success=False,
            message="Document ingestion failed.",
            error=str(error),
        )

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.post("/rag/search", response_model=SearchResponse)
def search_documents(request: SearchRequest):
    try:
        return rag_service.search(
            query=request.query,
            top_k=request.top_k,
            user_access_level=request.user_access_level,
            document_name=request.document_name,
            document_type=request.document_type,
            metadata_filters=request.metadata_filters,
        )

    except Exception as error:
        return SearchResponse(
            success=False,
            query=request.query,
            results=[],
            result_count=0,
            message="Local retrieval failed.",
            error=str(error),
        )