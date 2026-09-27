"""Retrieval routes. Both are real when stub mode is off: products (C14), substitutes (C26).

The stub survives for each of them under `STUB_MODE`, which is what keeps the committed
C02 contract tests measuring the contract rather than the index.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.deps import (
    V1_RESPONSES,
    get_app_settings,
    get_service_principal,
    get_unscoped_principal,
)
from jbg_ai.api.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    SubstitutesRequest,
    SubstitutesResponse,
)
from jbg_ai.config import Settings
from jbg_ai.db.engine import DatabaseNotConfiguredError
from jbg_ai.indexing.embeddings import EmbeddingClient
from jbg_ai.retrieval.errors import (
    InvalidFamilyIdError,
    InvalidPosIdError,
    RetrievalDependencyError,
    UnusableSourceProductError,
)
from jbg_ai.retrieval.orchestrator import (
    build_retrieval_embed_client,
    retrieve_products as run_product_retrieval,
)
from jbg_ai.retrieval.ports import ProductSearchPort
from jbg_ai.retrieval.projection import ProjectionFreshness
from jbg_ai.retrieval.search import SqlAlchemyProductSearch
from jbg_ai.retrieval.substitutes import (
    retrieve_substitutes as run_substitutes_retrieval,
)
from jbg_ai.stubs import retrieval_products_stub, retrieval_substitutes_stub

# `SUBSTITUTES_DELIVERED_BY` lived here to name the change in a 501. It went with the 501:
# the route is served, and a constant announcing a future delivery would now be a lie the
# next reader has to disprove. Checked by search before removing it, not by memory.

router = APIRouter(prefix="/v1/retrieval", tags=["retrieval"], responses=V1_RESPONSES)


def _missing(setting: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{setting} is required when STUB_MODE is false",
    )


def _require_real_retrieval_settings(request: Request, settings: Settings) -> None:
    injected_embed = getattr(request.app.state, "retrieval_embed", None)
    injected_search = getattr(request.app.state, "retrieval_search", None)
    if injected_embed is None and not settings.jpv_embedding_api_key:
        raise _missing("JPV_EMBEDDING_API_KEY")
    if injected_search is None and not settings.database_url:
        raise _missing("DATABASE_URL")


def _resolve_embed(request: Request, settings: Settings) -> EmbeddingClient:
    """Resolve, never construct: `create_app` builds the singleton once per process.

    Building one here is what kept the C11 cache empty forever — a client born with the request and
    dying with the response can never record a hit. The fallback survives only for an app
    assembled without the factory; it caches nothing across requests and is not the live path.
    """
    injected = getattr(request.app.state, "retrieval_embed", None)
    if injected is not None:
        return injected  # type: ignore[no-any-return]
    client = build_retrieval_embed_client(settings)
    request.app.state.retrieval_embed = client
    return client


def _resolve_search(request: Request, settings: Settings) -> ProductSearchPort:
    injected = getattr(request.app.state, "retrieval_search", None)
    if injected is not None:
        return injected  # type: ignore[no-any-return]
    return SqlAlchemyProductSearch(settings)


def _resolve_freshness(request: Request) -> ProjectionFreshness:
    """One freshness cache per application, not per process.

    Per process looks equivalent and is not: a process can hold more than one application —
    every test that builds a second one does — and they would then share a cached answer
    about a checkpoint they do not necessarily share. Per request would be worse still: the
    cache exists precisely so repeated retrievals stop spending a connection each on a value
    that changes at cron cadence, and one born with the request can never record a hit.
    """
    existing = getattr(request.app.state, "retrieval_freshness", None)
    if existing is not None:
        return existing  # type: ignore[no-any-return]
    freshness = ProjectionFreshness()
    request.app.state.retrieval_freshness = freshness
    return freshness


@router.post(
    "/products",
    response_model=RetrievalResponse,
    summary="Retrieve catalog candidates for a query",
)
async def retrieve_products(
    payload: RetrievalRequest,
    request: Request,
    # C40: this route takes a token with or without `pos_id`. Absent, the availability
    # prefilter does not apply — it does not match everything — and the response echoes the
    # absence. Substitutes below keeps `get_service_principal` and still rejects it.
    principal: ServicePrincipal = Depends(get_unscoped_principal),
    settings: Settings = Depends(get_app_settings),
) -> RetrievalResponse:
    """Over-fetch candidates so .NET can filter and still fill a page of `top_k`.

    `payload.pos_id` is ignored on purpose: the scope comes from the token.
    """
    if settings.stub_mode:
        return retrieval_products_stub(payload, principal)

    _require_real_retrieval_settings(request, settings)
    try:
        return await run_product_retrieval(
            payload,
            principal,
            settings=settings,
            embed=_resolve_embed(request, settings),
            search=_resolve_search(request, settings),
            freshness=_resolve_freshness(request),
        )
    except InvalidFamilyIdError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except InvalidPosIdError as exc:
        # 422 and never an unscoped search. A token whose point of sale cannot be read is a
        # mis-issued token; widening it to the whole catalogue would answer a broken claim
        # with every other shop's assortment.
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except RetrievalDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


# Substitutes over the STORED embedding: no provider is called on this path.
#
# `payload.pos_id` is ignored on purpose, like the products route: the scope comes from the
# token. The scope is read as a SIGNAL only — availability demotes a candidate and never
# removes it, and excluding on stock belongs to .NET, which owns the stock (C34).
#
# **The projection age travels in each result's `debug.notes`** and not in a response field.
# `RetrievalResponse` carries `projection_age_seconds`; `SubstitutesResponse` does not, and
# `ai-service/openapi.json` is frozen — adding the field would regenerate the snapshot that
# `test_openapi_snapshot_is_stable` guards. `debug` is in the frozen contract already, which
# makes it the one place the age can be declared without moving anything.
#
# No embedding settings are required here, only the database: the route that needs a
# provider is the one that embeds a query, and this one embeds nothing.
#
# **This is a comment and not a docstring, which is not a style choice.** FastAPI publishes a
# handler's docstring as the operation's `description`, and this operation has none in the
# frozen snapshot — it was written when the handler was a two-line stub. Writing the
# explanation here caught exactly that: the snapshot test went red on a `description` that
# appeared out of nowhere. The sibling handler above keeps its docstring because the snapshot
# already carries it.
@router.post(
    "/substitutes",
    response_model=SubstitutesResponse,
    summary="Retrieve interchangeable products for a reference product",
)
async def retrieve_substitutes(
    payload: SubstitutesRequest,
    request: Request,
    principal: ServicePrincipal = Depends(get_service_principal),
    settings: Settings = Depends(get_app_settings),
) -> SubstitutesResponse:
    if settings.stub_mode:
        return retrieval_substitutes_stub(payload, principal)

    injected_search = getattr(request.app.state, "retrieval_search", None)
    if injected_search is None and not settings.database_url:
        raise _missing("DATABASE_URL")

    try:
        return await run_substitutes_retrieval(
            payload,
            principal,
            settings=settings,
            search=_resolve_search(request, settings),
            freshness=_resolve_freshness(request),
        )
    except UnusableSourceProductError as exc:
        # 422 and not 404: the status is already documented for this route in the frozen
        # snapshot, and it is what its two sibling errors use — the body named something
        # this service cannot process. Never a 200 with an empty list; the detail names
        # which of the three causes applies.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InvalidFamilyIdError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InvalidPosIdError as exc:
        # A token whose point of sale cannot be read is a mis-issued token; the products
        # route refuses it for the same reason and must not be contradicted here.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except RetrievalDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
