"""Shared contract pieces reused across the `/v1` domains.

Boundary rule: jbg-ai computes similarity and writes prose; the .NET API owns
price, stock and permissions. No model here carries a price or stock figure.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from jbg_ai.assist.constants import PRICE_PLACEHOLDER, STOCK_PLACEHOLDER

__all__ = ["PRICE_PLACEHOLDER", "STOCK_PLACEHOLDER", "ScopedResponse", "Usage"]


class Usage(BaseModel):
    """Model usage reported by generative routes; zeroed while stubs are served."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    model: str | None = Field(
        default=None, description="Provider model identifier, null while stubbed"
    )


class DebugInfo(BaseModel):
    """Optional retrieval diagnostics; minimally filled by the stubs."""

    vector_score: float | None = None
    lexical_score: float | None = None
    rerank_score: float | None = None
    notes: list[str] = Field(default_factory=list)


class TracedResponse(BaseModel):
    """Every response carries the correlation id the caller can log against."""

    trace_id: str = Field(..., description="Correlation id, from the token claim when present")


class ScopedResponse(TracedResponse):
    """Responses of point-of-sale scoped domains echo the scope actually applied."""

    effective_pos_id: str = Field(
        ...,
        description="Scope applied by the handler; always the token claim, never the body value",
    )
