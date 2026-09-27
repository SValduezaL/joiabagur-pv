"""Retrieval contracts: product search and substitutes.

`top_k` is the page size the .NET API wants *after* hydrating and filtering;
the retriever over-fetches and reports what it produced in `candidates_returned`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from jbg_ai.api.schemas.common import DebugInfo, ScopedResponse

MAX_TOP_K = 50


class RetrievalMode(str, Enum):
    HYBRID = "hybrid"
    VECTOR = "vector"
    LEXICAL = "lexical"


class RetrievalFilters(BaseModel):
    """Catalog-side filters only. Price and stock filtering stays on the .NET side."""

    materials: list[str] = Field(default_factory=list)
    category: str | None = None
    family_id: str | None = None
    exclude_product_ids: list[str] = Field(default_factory=list)


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=MAX_TOP_K, description="Page size wanted after hydration")
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    mode: RetrievalMode = RetrievalMode.HYBRID
    pos_id: str | None = Field(
        default=None,
        description="Accepted for client compatibility and ignored; scope comes from the token",
    )


class SubstitutesRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=MAX_TOP_K)
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    reason: str | None = Field(
        default=None, description="Why a substitute is needed, e.g. out of stock"
    )
    pos_id: str | None = Field(
        default=None,
        description="Accepted for client compatibility and ignored; scope comes from the token",
    )


class RetrievalResult(BaseModel):
    product_id: str
    sku: str
    score: float = Field(..., ge=0.0, le=1.0)
    match_reasons: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    family_id: str | None = Field(default=None, description="Null when the family is unknown")
    variant_label: str | None = Field(default=None, description="Null when the variant is unknown")
    debug: DebugInfo | None = None


class SimilaritySignals(BaseModel):
    """Why two products are considered interchangeable. No price signal by design."""

    material_overlap: float = Field(..., ge=0.0, le=1.0)
    style_similarity: float = Field(..., ge=0.0, le=1.0)
    visual_similarity: float | None = Field(default=None, ge=0.0, le=1.0)
    family_match: bool = False


class SubstituteResult(RetrievalResult):
    similarity_signals: SimilaritySignals


class RetrievalResponse(ScopedResponse):
    results: list[RetrievalResult]
    candidates_returned: int = Field(..., ge=0, description="Candidates the retriever produced")
    low_confidence: bool = False
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Codes of the closed warning vocabulary that describe the QUERY rather than a "
            "piece. Today only `filters_too_narrow`: the query is answerable and the caller's "
            "own catalog-side filters are what left almost nothing. It is emitted here and not "
            "only on the generative route because the decision belongs to retrieval, and every "
            "path that accepts filters can hit it. An abstention is a different statement and "
            "never carries it: that one says the description found nothing."
        ),
    )
    projection_age_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Seconds since the point-of-sale availability projection was last synchronised. "
            "Null when the prefilter did not run. Taken from the drain checkpoint and never "
            "from the projection rows: the feed is incremental, so a row's timestamp records "
            "when that assignment last changed rather than when the projection was last read, "
            "and would report months on a projection synchronised seconds ago. Above the "
            "configured ceiling the point-of-sale scope is not applied for that request and "
            "this field is how the caller can tell."
        ),
    )


class SubstitutesResponse(ScopedResponse):
    results: list[SubstituteResult]
    candidates_returned: int = Field(..., ge=0)
    low_confidence: bool = False
