from typing import Optional, Any
from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    duplicate: bool = False
    duplicate_of: Optional[str] = None
    total_pages: int = 0
    chunks_indexed: int = 0
    ocr_used: bool = False
    ocr_confidence: Optional[float] = None
    access_classification: Optional[str] = None
    message: str
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k: int = Field(default=5, ge=1, le=20)

    # Example: caller role/classification clearance
    user_access_level: str = "INTERNAL"

    # Optional filters
    document_name: Optional[str] = None
    document_type: Optional[str] = None
    metadata_filters: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    document: str
    document_id: str
    page: Optional[int] = None
    chunk_id: str
    content: str
    score: float
    retrieval_confidence: float
    metadata: dict[str, Any]
    access_classification: str
    ocr_confidence: Optional[float] = None


class SearchResponse(BaseModel):
    success: bool
    query: str
    results: list[SearchResult] = Field(default_factory=list)
    result_count: int = 0
    message: str
    error: Optional[str] = None