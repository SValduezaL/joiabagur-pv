"""Sale assistance routes. Real since C30a, and writing prose since C30b.

`DELIVERED_BY` went with the 501, exactly as `SUBSTITUTES_DELIVERED_BY` did when C26 served
its route: a constant announcing a future delivery, left behind on a route that answers, is
a lie the next reader has to disprove. Checked by search before removing it, not by memory.

**The generation layer is a dependency this route can serve without.** With no provider
credential configured it answers exactly what C30a answered — structure, warnings and
citations, empty argument, absent prompt version — rather than 503, because the half of the
response that matters is already computed and correct. That is also the rollback: removing the
client leaves the route in C30a's behaviour without touching a schema. A provider that is
configured and then fails degrades the same way, from inside the layer, and never as a 5xx.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.deps import (
    V1_RESPONSES,
    get_app_settings,
    get_service_principal,
    get_unscoped_principal,
)
from jbg_ai.api.schemas.assist import (
    AgentAssistRequest,
    AgentAssistResponse,
    AssistRequest,
    AssistResponse,
)
from jbg_ai.assist.agent import AgentBudgets, agent_response, run_agent
from jbg_ai.assist.agent_llm import AgentLlm, LiteLlmAgentClient
from jbg_ai.assist.constants import MAX_PITCH_PROVIDER_CALLS
from jbg_ai.assist.errors import (
    NoAnchorError,
    TranscriptError,
    UnusableAnchorProductError,
)
from jbg_ai.assist.tools import build_registry
from jbg_ai.assist.transcript import turns_from
from jbg_ai.assist.llm import AssistLlm, LiteLlmAssistClient
from jbg_ai.assist.router_llm import LiteLlmRouterClient, RouterLlm
from jbg_ai.assist.orchestrator import assist_sale as run_assist_sale
from jbg_ai.config import Settings
from jbg_ai.db.engine import DatabaseNotConfiguredError
from jbg_ai.indexing.embeddings import EmbeddingClient
from jbg_ai.knowledge.errors import KnowledgeSearchError
from jbg_ai.knowledge.search import KnowledgeSearchIndex, SqlAlchemyKnowledgeIndex
from jbg_ai.retrieval.errors import (
    InvalidFamilyIdError,
    InvalidPosIdError,
    RetrievalDependencyError,
)
from jbg_ai.retrieval.orchestrator import build_retrieval_embed_client
from jbg_ai.retrieval.ports import ProductSearchPort
from jbg_ai.retrieval.search import SqlAlchemyProductSearch
from jbg_ai.stubs import assist_agent_stub, assist_sale_stub

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/assist", tags=["assist"], responses=V1_RESPONSES)


def _missing(setting: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{setting} is required when STUB_MODE is false",
    )


def _require_real_settings(request: Request, settings: Settings) -> None:
    injected_embed = getattr(request.app.state, "retrieval_embed", None)
    injected_search = getattr(request.app.state, "retrieval_search", None)
    if injected_embed is None and not settings.jpv_embedding_api_key:
        raise _missing("JPV_EMBEDDING_API_KEY")
    if injected_search is None and not settings.database_url:
        raise _missing("DATABASE_URL")


def _resolve_embed(request: Request, settings: Settings) -> EmbeddingClient:
    """The SAME singleton the retrieval route resolves, and sharing it is the point.

    Measured: the client's bounded cache is keyed on a hash of the text plus the model and
    version, and both paths compose an identical `model_version_key`. So a piece-and-question
    request that embeds its question for the retrieval finds that vector already cached when
    the knowledge search asks for it — **one provider call, not two** — provided both are
    handed the same stripped text, which `assist_sale` guarantees.
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


def _resolve_knowledge(request: Request, settings: Settings) -> KnowledgeSearchIndex:
    injected = getattr(request.app.state, "knowledge_index", None)
    if injected is not None:
        return injected  # type: ignore[no-any-return]
    return SqlAlchemyKnowledgeIndex(settings)


def _resolve_pitch_client(request: Request, settings: Settings) -> AssistLlm | None:
    """The generation client, or **None**, which is a deployment state and not a failure.

    With no provider credential at all the route serves exactly what C30a served — structure,
    warnings and citations, with an empty argument and an absent prompt version — instead of
    answering 503 the way the paths that cannot work without their credential do. The
    difference is that those paths have nothing to return and this one has most of the
    response already computed and correct.

    **Its own credential, with a fallback that is logged rather than silent.**
    `JPV_ASSIST_LLM_API_KEY` bills, rate-limits and rotates counter-side generation apart from
    C09 enrichment, which is worth having: the two have different shapes — one is a batch with
    nobody waiting, the other is a call with a customer in front of it. It is **optional** on
    purpose: requiring it would stop an existing deployment generating the day the field
    appeared, and would do it invisibly, because the layer degrades to 200 without prose rather
    than failing. So it falls back to `JPV_RAG_LLM_API_KEY` — and the line below says which one
    is in force, so "we have separate credentials" is something a deployment can check instead
    of assume.

    **Its own model too**, and never `JPV_RAG_LLM_MODEL`: that setting is C09's enrichment
    model, and inheriting it would let a change to enrichment move the model of a counter-side
    call whose cost, latency and rejection rate were measured on another.
    """
    injected = getattr(request.app.state, "assist_pitch_client", None)
    if injected is not None:
        return injected  # type: ignore[no-any-return]

    dedicated = bool(settings.jpv_assist_llm_api_key)
    api_key = settings.jpv_assist_llm_api_key or settings.jpv_rag_llm_api_key
    if not api_key:
        return None
    client = LiteLlmAssistClient(
        api_key=api_key,
        # The base URL stays C09's: it names the PROVIDER endpoint, not the account, so a
        # separate credential against the same provider needs no second one. A deployment that
        # ever points the two at different gateways needs a field here, and would notice.
        base_url=settings.jpv_rag_llm_base_url,
        model=settings.jpv_assist_llm_model,
        # Settings supplies the default and the value travels by parameter, the pattern C20,
        # C23 and C25 established: an evaluation can sweep it inside one process.
        timeout=settings.jpv_assist_pitch_timeout_seconds,
    )
    # Once per process, never per request, and it carries no secret — only WHICH of the two
    # credentials was resolved, which is the whole point of having two.
    logger.info(
        "stage=assist_client model=%s timeout_s=%s credential=%s",
        client.model_id,
        settings.jpv_assist_pitch_timeout_seconds,
        "assist" if dedicated else "rag_fallback",
    )
    request.app.state.assist_pitch_client = client
    return client


def _resolve_router_client(request: Request, settings: Settings) -> RouterLlm | None:
    """The classifier, or **None**, which is a deployment state and not a failure. C31.

    With no credential at all the classifier is not constructed and the free-query mode serves
    exactly what C30b served: an unclassified intent, both indexes consulted, the abstention
    rule as the net, and no argument. That is the fail-open, the ablation and the rollback in
    one — removing the credential is how a deployment goes back.

    **Its own credential, with a chain that is logged rather than silent.** C30b opened
    `JPV_ASSIST_LLM_API_KEY` falling back to `JPV_RAG_LLM_API_KEY`; this prepends
    `JPV_ROUTER_LLM_API_KEY` to the same chain, so a deployment that sets none of them keeps
    working and one that sets the new one bills the classifier apart. The line below says which
    of the three is in force — the whole point of having three — and carries no secret.

    **Its own model too**, and never `JPV_ASSIST_LLM_MODEL`: around thirty output tokens against
    a paragraph is not the same call, and sharing the variable would make any cost comparison
    between them false.
    """
    injected = getattr(request.app.state, "assist_router_client", None)
    if injected is not None:
        return injected  # type: ignore[no-any-return]

    if settings.jpv_router_llm_api_key:
        api_key, credential = settings.jpv_router_llm_api_key, "router"
    elif settings.jpv_assist_llm_api_key:
        api_key, credential = settings.jpv_assist_llm_api_key, "assist_fallback"
    elif settings.jpv_rag_llm_api_key:
        api_key, credential = settings.jpv_rag_llm_api_key, "rag_fallback"
    else:
        return None

    client = LiteLlmRouterClient(
        api_key=api_key,
        # The base URL stays C09's, for the reason the generation client gives: it names the
        # PROVIDER endpoint and not the account.
        base_url=settings.jpv_rag_llm_base_url,
        model=settings.jpv_router_llm_model,
        timeout=settings.jpv_router_timeout_seconds,
    )
    # Once per process, never per request, and it carries no secret and no query — only WHICH
    # credential was resolved. `stage=router_client` absent in the container log says no client
    # was built and the route behaves as C30b's, which is the verification the deployment needs
    # without opening a console or reading a key.
    logger.info(
        "stage=router_client model=%s timeout_s=%s credential=%s",
        client.model_id,
        settings.jpv_router_timeout_seconds,
        credential,
    )
    request.app.state.assist_router_client = client
    return client


@router.post(
    "/sale",
    response_model=AssistResponse,
    summary="Assist a sale with family-grouped candidates and a pitch",
)
async def assist_sale(
    payload: AssistRequest,
    request: Request,
    # C40: the free-query mode may be scoped to every shop, so `pos_id` is accepted and no
    # longer demanded. The anchored modes still send one, because a card reports that shop's
    # stock. The agent route below keeps the strict dependency.
    principal: ServicePrincipal = Depends(get_unscoped_principal),
    settings: Settings = Depends(get_app_settings),
) -> AssistResponse:
    """Group candidates by family; the pitch keeps price and stock as placeholders."""
    if settings.stub_mode:
        return assist_sale_stub(payload, principal)

    _require_real_settings(request, settings)
    try:
        return await run_assist_sale(
            payload,
            principal,
            settings=settings,
            embed=_resolve_embed(request, settings),
            search=_resolve_search(request, settings),
            knowledge=_resolve_knowledge(request, settings),
            pitch_client=_resolve_pitch_client(request, settings),
            router_client=_resolve_router_client(request, settings),
        )
    except UnusableAnchorProductError as exc:
        # 422 and not 404, like the substitutes route: the body named something this service
        # cannot process. Never a 200 with `abstained` set — that would claim the catalogue
        # has no answer when what is broken is the piece.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NoAnchorError as exc:
        # Unreachable through HTTP — the request model rejects it first — and kept because
        # the layer is also a callable and the two paths must answer the same way.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InvalidFamilyIdError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InvalidPosIdError as exc:
        # A token whose point of sale cannot be read is a mis-issued token. The retrieval
        # routes refuse it for the same reason and must not be contradicted here.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except (RetrievalDependencyError, KnowledgeSearchError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def _resolve_agent_client(request: Request, settings: Settings) -> AgentLlm | None:
    """The loop's client, or **None**, which is a deployment state and not a failure. C32b.

    With no credential at all the loop is not constructed and `POST /v1/assist/agent` answers
    the shape without running it, rather than 503. That is the fail-open, **the ablation and
    the rollback in one**: removing the credential is how a deployment returns to the
    behaviour that preceded this capability, and the row it produces is the one the comparison
    against the deterministic pipeline needs.

    **Its own credential, with a chain that is logged rather than silent.** C30b opened
    `JPV_ASSIST_LLM_API_KEY` falling back to `JPV_RAG_LLM_API_KEY` and C31 prepended
    `JPV_ROUTER_LLM_API_KEY` to its own chain; this prepends `JPV_AGENT_LLM_API_KEY` to the
    generation chain — **agent, then assist, then rag** — so a deployment that sets none keeps
    working and one that sets the new one bills the loop apart. The classifier's credential is
    deliberately **not** a link: a request of this route resolves two clients, and letting one
    fall back to the other would make the cost of the two stages impossible to tell apart.

    **Its own model too**, and never the argument's nor the classifier's: choosing which tool
    to call is a harder task than choosing which label, and sharing a variable would make any
    comparison of cost between the three false.
    """
    injected = getattr(request.app.state, "assist_agent_client", None)
    if injected is not None:
        return injected  # type: ignore[no-any-return]

    if settings.jpv_agent_llm_api_key:
        api_key, credential = settings.jpv_agent_llm_api_key, "agent"
    elif settings.jpv_assist_llm_api_key:
        api_key, credential = settings.jpv_assist_llm_api_key, "assist_fallback"
    elif settings.jpv_rag_llm_api_key:
        api_key, credential = settings.jpv_rag_llm_api_key, "rag_fallback"
    else:
        return None

    client = LiteLlmAgentClient(
        api_key=api_key,
        # The base URL stays C09's, for the reason the two sibling clients give: it names the
        # PROVIDER endpoint and not the account.
        base_url=settings.jpv_rag_llm_base_url,
        model=settings.jpv_agent_llm_model,
        timeout=settings.jpv_agent_timeout_seconds,
    )
    # Once per process, never per request, and it carries no secret and no transcript — only
    # WHICH link was resolved. `stage=agent_client` absent from the container log says no loop
    # client was built and the route degrades, which is the verification a deployment needs
    # without opening a console or reading a key.
    logger.info(
        "stage=agent_client model=%s timeout_s=%s credential=%s",
        client.model_id,
        settings.jpv_agent_timeout_seconds,
        credential,
    )
    request.app.state.assist_agent_client = client
    return client


@router.post(
    "/agent",
    response_model=AgentAssistResponse,
    summary="Assist a sale with an agent loop over a multi-turn transcript",
)
async def assist_agent(
    payload: AgentAssistRequest,
    request: Request,
    # **Unscoped since C42, joining the deterministic route that was widened in C40.** This was
    # the only route of the assistance family left out, because at the time it had no consumer —
    # and a panel offering the every-shop scope on the agent would otherwise be refused by the
    # very route its sibling panel is served by. The absence of the claim means «do not apply the
    # availability prefilter» and never a wildcard: with no shop the availability tool can only
    # report that no scope applies, so the loop cannot pivot to substitutes. That is a
    # consequence of the data, not a behaviour anybody simulates. Every other `/v1` route that
    # operates inside one shop — substitutes and inventory — still requires the claim.
    principal: ServicePrincipal = Depends(get_unscoped_principal),
    settings: Settings = Depends(get_app_settings),
) -> AgentAssistResponse:
    """Run the loop over the transcript; the pitch keeps price and stock as placeholders.

    **A route of its own, and the separation is the decision this change turns on.** Its worst
    case is several times the latency the deterministic route declares, so a flag on that route
    would put a long path in the one a counter calls synchronously — and the comparison this
    capability exists to enable needs both to stay runnable over the same set.

    The error mapping is the deterministic route's, extended by one: a transcript over its
    declared caps is a 422, the status this service already uses for a body naming something
    it cannot process. It is unreachable through HTTP — the request model refuses it first —
    and it is here because the layer is also a callable.
    """
    if settings.stub_mode:
        return assist_agent_stub(payload, principal)

    _require_real_settings(request, settings)
    try:
        run = await run_agent(
            turns_from([(turn.role, turn.text) for turn in payload.turns]),
            principal,
            registry=build_registry(
                principal=principal,
                settings=settings,
                embed=_resolve_embed(request, settings),
                search=_resolve_search(request, settings),
                knowledge=_resolve_knowledge(request, settings),
            ),
            agent_client=_resolve_agent_client(request, settings),
            router_client=_resolve_router_client(request, settings),
            pitch_client=_resolve_pitch_client(request, settings),
            # The argument's reserve from the timeout its client is actually built with, so
            # the deadline holds for the request as configured and not only for the default.
            budgets=AgentBudgets(
                pitch_reserve_seconds=MAX_PITCH_PROVIDER_CALLS
                * settings.jpv_assist_pitch_timeout_seconds
            ),
        )
    except TranscriptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InvalidPosIdError as exc:
        # A token whose point of sale cannot be read is a mis-issued token. The sibling routes
        # refuse it for the same reason and must not be contradicted here.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DatabaseNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except (RetrievalDependencyError, KnowledgeSearchError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return agent_response(run, principal)
