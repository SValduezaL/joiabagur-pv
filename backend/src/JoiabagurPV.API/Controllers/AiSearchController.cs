using FluentValidation;
using JoiabagurPV.API.Extensions;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;

namespace JoiabagurPV.API.Controllers;

/// <summary>
/// Assisted catalog search. Exposes exactly one operation: running a natural-language search
/// for one point of sale.
/// </summary>
/// <remarks>
/// <para>
/// The AI service proposes candidates; this endpoint applies the truth. Price, stock and what
/// the shop actually carries come from the transactional catalog, never from the AI response —
/// which is contractually forbidden from carrying them.
/// </para>
/// <para>
/// The search never fails because of the AI. Every failure mode of the gateway degrades to a
/// lexical searcher and is reported through <c>aiAvailable</c>, so the caller can say so on
/// screen rather than showing an error.
/// </para>
/// <para>
/// The route carries no version, like the other controllers under <c>api/ai</c>. Versioning is
/// applied at the boundary that needs it — the frozen contract with the separately deployed
/// <c>jbg-ai</c> — and not between a SPA and an API that ship together.
/// </para>
/// </remarks>
[ApiController]
[Route("api/ai/search")]
[Authorize]
[EnableRateLimiting(RateLimitPolicies.AiSearch)]
public class AiSearchController : ControllerBase
{
    private readonly IAssistedSearchService _searchService;
    private readonly ICurrentUserService _currentUserService;
    private readonly IValidator<AssistedSearchRequest> _validator;
    private readonly IFreeQuerySearchService _freeQuerySearchService;
    private readonly IAgentAssistService _agentAssistService;
    private readonly IValidator<AgentAssistRequest> _agentValidator;

    public AiSearchController(
        IAssistedSearchService searchService,
        ICurrentUserService currentUserService,
        IValidator<AssistedSearchRequest> validator,
        IFreeQuerySearchService freeQuerySearchService,
        IAgentAssistService agentAssistService,
        IValidator<AgentAssistRequest> agentValidator)
    {
        _searchService = searchService;
        _currentUserService = currentUserService;
        _validator = validator;
        _freeQuerySearchService = freeQuerySearchService;
        _agentAssistService = agentAssistService;
        _agentValidator = agentValidator;
    }

    /// <summary>
    /// Runs an assisted search for a point of sale.
    /// </summary>
    /// <param name="request">Query, point of sale, page size, episode and quick filters.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Results in retrieval order, plus the state of the assisted path.</returns>
    [HttpPost]
    [ProducesResponseType(typeof(AssistedSearchResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status429TooManyRequests)]
    public async Task<IActionResult> Search(
        [FromBody] AssistedSearchRequest? request,
        CancellationToken cancellationToken)
    {
        if (!_currentUserService.UserId.HasValue)
        {
            return Unauthorized(new { message = "User not authenticated." });
        }

        // SuppressModelStateInvalidFilter is on, so a body that fails to bind still reaches the
        // action as null and FluentValidation would throw on it.
        if (request is null)
        {
            return BadRequest(new { errors = new[] { "La petición de búsqueda es obligatoria." } });
        }

        // Validated explicitly: this project registers validators but wires no automatic
        // pipeline, so an uninvoked validator is worse than none — it looks like validation.
        var validationResult = await _validator.ValidateAsync(request, cancellationToken);
        if (!validationResult.IsValid)
        {
            return BadRequest(new { errors = validationResult.Errors.Select(e => e.ErrorMessage) });
        }

        var result = await _searchService.SearchAsync(
            request,
            _currentUserService.UserId.Value,
            _currentUserService.Role ?? "Operator",
            _currentUserService.IsAdmin,
            cancellationToken);

        return result.Outcome switch
        {
            // The point of sale exists but this operator is not assigned to it. Administrators
            // are granted the exception inside the service, explicitly and only for active
            // points of sale.
            AssistedSearchOutcome.PointOfSaleForbidden => Forbid(),

            // Unknown or inactive point of sale. A validation problem rather than an
            // authorisation one: nobody, whatever their role, can search a shop that is closed.
            AssistedSearchOutcome.PointOfSaleUnavailable => BadRequest(new
            {
                errors = new[] { "El punto de venta no existe o no está activo." }
            }),

            _ => Ok(result.Response)
        };
    }

    /// <summary>
    /// Answers a free-text query: the assisted route of the panel's toggle. C40.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A second endpoint rather than a <c>mode</c> field on the first, and the reason is
    /// mechanical: <strong>a rate limit is an attribute of an endpoint in ASP.NET</strong>, so one
    /// route would have to pick a single allowance — 30/min lets an operator burn thirty
    /// generations, 10/min strangles the cheap path — and the time budget has the same problem.
    /// Four properties already differ: the switch, the allowance, the budget and the circuit.
    /// </para>
    /// <para>
    /// Its own rate-limiting policy, and not the card's: the card is opened once per piece and
    /// this panel is used in bursts. A shared quota would leave whichever one an operator reached
    /// second unable to work, with nothing on screen explaining why.
    /// </para>
    /// <para>
    /// <strong>A 429 is not an outage.</strong> Exceeding the allowance has to stay distinguishable
    /// from the AI being unavailable — one is the system protecting itself and resolves in
    /// seconds, the other is a fault — so the throttle answers 429 while every AI failure answers
    /// 200 with a reason.
    /// </para>
    /// </remarks>
    [HttpPost("assisted")]
    [EnableRateLimiting(RateLimitPolicies.AiFreeQuerySearch)]
    [ProducesResponseType(typeof(FreeQuerySearchResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status429TooManyRequests)]
    public async Task<IActionResult> AssistedSearch(
        [FromBody] FreeQuerySearchRequest? request,
        CancellationToken cancellationToken)
    {
        if (!_currentUserService.UserId.HasValue)
        {
            return Unauthorized(new { message = "User not authenticated." });
        }

        if (request is null)
        {
            return BadRequest(new { errors = new[] { "La petición de búsqueda es obligatoria." } });
        }

        if (string.IsNullOrWhiteSpace(request.Query))
        {
            return BadRequest(new { errors = new[] { "La consulta es obligatoria." } });
        }

        if (request.Query.Length > FreeQuerySearchRequest.MaxQueryLength)
        {
            return BadRequest(new
            {
                errors = new[]
                {
                    $"La consulta no puede superar los {FreeQuerySearchRequest.MaxQueryLength} caracteres."
                }
            });
        }

        // **Absent means every shop; empty is a malformed request.** The distinction is the same
        // one the token claim draws, and for the same reason: a caller that meant «all of them»
        // omits the field, and a caller that sent `Guid.Empty` sent a value that identifies no
        // shop. Reading the second as the first would turn a client bug into a wider search.
        if (request.PointOfSaleId == Guid.Empty)
        {
            return BadRequest(new
            {
                errors = new[]
                {
                    "El punto de venta no es válido. Omítelo para buscar en todas las tiendas."
                }
            });
        }

        var result = await _freeQuerySearchService.SearchAsync(
            request,
            _currentUserService.UserId.Value,
            _currentUserService.Role ?? "Operator",
            _currentUserService.IsAdmin,
            cancellationToken);

        return result.Outcome switch
        {
            FreeQuerySearchOutcome.PointOfSaleForbidden => Forbid(),

            FreeQuerySearchOutcome.PointOfSaleUnavailable => BadRequest(new
            {
                errors = new[] { "El punto de venta no existe o no está activo." }
            }),

            _ => Ok(result.Response)
        };
    }

    /// <summary>
    /// Answers the last turn of a sale-agent conversation. C42.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <strong>Authorised by exactly the rule the free-query route uses</strong>, and copied rather
    /// than tightened: two sibling panels with two different authorisation rules break without any
    /// test failing. Both roles, the every-shop scope open to both, and the boundary that is actually
    /// protected is the narrow one — a caller may not name a shop they are not assigned to, and that
    /// is refused before any call is made.
    /// </para>
    /// <para>
    /// <strong>The three transcript caps are validated here, before the call.</strong> The AI service
    /// would answer 422, which is correct and useless: the caller would have paid the round trip to
    /// learn its request was malformed, and on this route that round trip competes for a quota that
    /// admits about one request per minute. The total in particular sums <em>every</em> turn, the
    /// assistant's included, and is not implied by the other two.
    /// </para>
    /// <para>
    /// Its own rate-limiting policy, a fourth one, because the binding constraint is the
    /// tokens-per-minute quota rather than the money. <strong>A 429 is not an outage</strong>: the
    /// throttle answers 429 while every AI failure answers 200 with a reason, and so does every
    /// degradation the loop reports inside a successful response.
    /// </para>
    /// </remarks>
    [HttpPost("agent")]
    [EnableRateLimiting(RateLimitPolicies.AiAgentAssist)]
    [ProducesResponseType(typeof(AgentAssistResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status429TooManyRequests)]
    public async Task<IActionResult> Agent(
        [FromBody] AgentAssistRequest? request,
        CancellationToken cancellationToken)
    {
        if (!_currentUserService.UserId.HasValue)
        {
            return Unauthorized(new { message = "User not authenticated." });
        }

        if (request is null)
        {
            return BadRequest(new { errors = new[] { "La conversación es obligatoria." } });
        }

        // **Absent means every shop; empty is a malformed request.** The same distinction the
        // free-query route draws, and for the same reason: a caller that meant «all of them» omits
        // the field, and a caller that sent `Guid.Empty` sent a value identifying no shop.
        if (request.PointOfSaleId == Guid.Empty)
        {
            return BadRequest(new
            {
                errors = new[]
                {
                    "El punto de venta no es válido. Omítelo para conversar sobre todas las tiendas."
                }
            });
        }

        // The three caps, in Spanish, and **before the service is called at all** — which is what
        // the test for this asserts: not only the 400, but that no gateway call was made.
        var validation = await _agentValidator.ValidateAsync(request, cancellationToken);
        if (!validation.IsValid)
        {
            return BadRequest(new
            {
                errors = validation.Errors.Select(error => error.ErrorMessage).ToArray()
            });
        }

        var result = await _agentAssistService.AnswerAsync(
            request,
            _currentUserService.UserId.Value,
            _currentUserService.Role ?? "Operator",
            _currentUserService.IsAdmin,
            cancellationToken);

        return result.Outcome switch
        {
            AgentAssistOutcome.PointOfSaleForbidden => Forbid(),

            AgentAssistOutcome.PointOfSaleUnavailable => BadRequest(new
            {
                errors = new[] { "El punto de venta no existe o no está activo." }
            }),

            _ => Ok(result.Response)
        };
    }

    /// <summary>
    /// Reports which assisted paths are switched on for a point of sale, before any search.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Makes <strong>no call to the AI service</strong> and consumes no quota: it reads two
    /// configuration switches. That is the whole point — the screen must be able to say the
    /// assisted answer is unavailable without spending one of the ten calls a minute it would
    /// need to find out, and without the operator discovering it by pressing a button that fails.
    /// </para>
    /// <para>
    /// Rate limiting is disabled on this action rather than left to inherit the controller's
    /// policy. Inheriting it would mean that checking whether you may search costs a search,
    /// which would let a panel that polls availability exhaust the quota for the thing it was
    /// checking on.
    /// </para>
    /// <para>
    /// No point-of-sale assignment check: this answers about configuration, not about stock,
    /// prices or anything else a shop holds. Refusing it for an unassigned shop would leak the
    /// same bit it is being asked for, and the search itself remains authorised as before.
    /// </para>
    /// </remarks>
    /// <param name="pointOfSaleId">
    /// The point of sale to report on, or omitted for the scope covering every one of them.
    /// </param>
    [HttpGet("availability")]
    [DisableRateLimiting]
    [ProducesResponseType(typeof(AiSearchAvailabilityResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public IActionResult Availability([FromQuery] Guid? pointOfSaleId)
    {
        if (!_currentUserService.UserId.HasValue)
        {
            return Unauthorized(new { message = "User not authenticated." });
        }

        // **Absent means every shop; blank is a malformed request.** The same distinction the
        // free-query route draws, word for word and for the same reason: a caller that meant «all
        // of them» omits the field, and a caller that sent an empty identifier sent a value that
        // names no shop. Reading the second as the first would turn a client bug into a wider
        // answer — and it is the distinction that makes this scope safe, since an absent point of
        // sale leaves the availability prefilter unapplied rather than matching everything.
        //
        // Until C40_FIX this refused the absence too, so a screen offering the wider scope had
        // nothing to read and showed the generative path disabled with no reason: the failure this
        // route exists to prevent, reappearing one scope along.
        //
        // **And absence is the field not being there — not the field being there with nothing
        // usable in it.** A `Guid?` swallows a query value it cannot parse — an empty string,
        // whitespace, a typo, a truncated identifier — and binds `null`, which since C40_FIX is a
        // *meaning* rather than a missing field; `SuppressModelStateInvalidFilter` is on globally,
        // so nothing else refuses it either. While the parameter was a non-nullable `Guid` the
        // guard above caught all of it, because a failed bind left `Guid.Empty`. Making the
        // parameter nullable removed that net, so the key being present is checked here.
        if (pointOfSaleId == Guid.Empty
            || (pointOfSaleId is null && Request.Query.ContainsKey(nameof(pointOfSaleId))))
        {
            return BadRequest(new
            {
                errors = new[]
                {
                    "El punto de venta no es válido. Omítelo para consultar todas las tiendas."
                }
            });
        }

        return Ok(_searchService.GetAvailability(pointOfSaleId));
    }
}
