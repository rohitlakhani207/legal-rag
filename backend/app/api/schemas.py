from pydantic import BaseModel, Field

from app.retrieval.search import Mode


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    mode: Mode = Mode.HYBRID_RERANK
    top_k: int = Field(default=5, ge=1, le=20)


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    mode: Mode = Mode.HYBRID_RERANK
    top_k: int = Field(default=5, ge=1, le=10)


class Source(BaseModel):
    marker: int
    chunk_id: int
    document_id: str
    doc_short_name: str
    doc_title: str
    section_id: str
    section_title: str
    hierarchy: str
    citation: str
    content: str
    score: float
    vector_rank: int | None
    fulltext_rank: int | None
    rerank_score: float | None


class SearchResponse(BaseModel):
    query: str
    mode: Mode
    sources: list[Source]
    timings_ms: dict[str, float]


class CitationOut(BaseModel):
    marker: int
    chunk_id: int
    label: str


class AskResponse(BaseModel):
    question: str
    mode: Mode
    model: str
    answer: str
    abstained: bool
    citations: list[CitationOut]
    invalid_citation_markers: list[int]
    sources: list[Source]
    timings_ms: dict[str, float]


class DocumentOut(BaseModel):
    id: str
    title: str
    short_name: str
    jurisdiction: str | None
    source_url: str | None
    sections: int
    chunks: int


class UploadResponse(BaseModel):
    id: str
    sections: int
    chunks: int
