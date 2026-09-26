using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Domain.Enums;
using JoiabagurPV.Domain.Interfaces.Repositories;
using JoiabagurPV.Domain.Interfaces.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace JoiabagurPV.Application.Services;

/// <summary>
/// Orchestrates one turn of a sale-agent conversation: the transcript out, the evidence back,
/// hydrated against the catalog and recorded under an origin of its own. C42.
/// </summary>
/// <remarks>
/// <para>
/// <strong>The consumer that did not exist.</strong> The agent loop has been delivered, tested and
/// measured against a real provider since C32b, and nothing called it: the gateway client carried
/// seven operations and none was this one. That is not a 3 % degradation, it is the whole path.
/// </para>
/// <para>
/// <strong>Never throws because of the AI</strong>, and on this route that covers one case more than
/// its sibling. Besides the gateway's failures, the loop reports two degradations <em>inside</em> a
/// successful response — its provider fell, or no agent credential is configured — and those arrive
/// as answers carrying their stop reason rather than as errors. The screen has copy for all ten stop
/// reasons precisely so that an answer that degraded still says something true.
/// </para>
/// <para>
/// <strong>The authority does not move.</strong> The AI service decides what to retrieve and writes
/// the argument; price and stock are this side's, per candidate and per shop. The qualitative
/// availability band the loop reads governs one thing only — whether it pivots to substitutes — and
/// never reaches the argument.
/// </para>
/// </remarks>
public class AgentAssistService : IAgentAssistService
{
    private readonly IAiGatewayClient _gateway;
    private readonly IAssistedSearchRepository _repository;
    private readonly IAssistedSearchResultProjector _projector;
    private readonly IUserPointOfSaleService _userPointOfSaleService;
    private readonly IProductSearchEventService _searchEventService;
    private readonly ITraceContextAccessor _traceContext;
    private readonly IOptionsMonitor<AiAgentAssistOptions> _options;
    private readonly IOptionsMonitor<AiFreeQuerySearchOptions> _pageOptions;
    private readonly TimeProvider _timeProvider;
    private readonly ILogger<AgentAssistService> _logger;

    public AgentAssistService(
        IAiGatewayClient gateway,
        IAssistedSearchRepository repository,
        IAssistedSearchResultProjector projector,
        IUserPointOfSaleService userPointOfSaleService,
        IProductSearchEventService searchEventService,
        ITraceContextAccessor traceContext,
        IOptionsMonitor<AiAgentAssistOptions> options,
        IOptionsMonitor<AiFreeQuerySearchOptions> pageOptions,
        TimeProvider timeProvider,
        ILogger<AgentAssistService> logger)
    {
        _gateway = gateway;
        _repository = repository;
        _projector = projector;
        _userPointOfSaleService = userPointOfSaleService;
        _searchEventService = searchEventService;
        _traceContext = traceContext;
        _options = options;
        _pageOptions = pageOptions;
        _timeProvider = timeProvider;
        _logger = logger;
    }

    /// <inheritdoc/>
    public async Task<AgentAssistResult> AnswerAsync(
        AgentAssistRequest request,
        Guid userId,
        string role,
        bool isAdmin,
        CancellationToken cancellationToken = default)
    {
        var startedAt = _timeProvider.GetTimestamp();
        var options = _options.CurrentValue;
        var pageOptions = _pageOptions.CurrentValue;

        var access = await AuthoriseAsync(request.PointOfSaleId, userId, isAdmin, cancellationToken);
        if (access is not null)
        {
            return access;
        }

        var pageSize = Math.Clamp(
            request.PageSize ?? pageOptions.DefaultPageSize, 1, pageOptions.MaxPageSize);

        AiAssistAgentResponse? ai = null;
        string? degradedReason = null;
        int? aiMs = null;

        // **Switched off costs no call and no quota**, and on this route the quota is the binding
        // constraint. The agent's own switch, never the assisted answer's: the two can be off
        // independently, which is exactly what the availability probe has to be able to report.
        if (!options.IsEnabledForScope(request.PointOfSaleId))
        {
            degradedReason = "switched_off";
        }
        else
        {
            var aiStartedAt = _timeProvider.GetTimestamp();
            (ai, degradedReason) = await CallAsync(request, options, userId, role, cancellationToken);
            aiMs = ElapsedMs(aiStartedAt);
        }

        var groups = ai is null
            ? []
            : await HydrateAsync(ai, request.PointOfSaleId, pageSize, cancellationToken);

        var candidates = ai?.Groups.Sum(group => group.Members.Count) ?? 0;
        var survived = groups.Sum(group => group.Members.Count);

        // Captured before telemetry: recording is work this figure must not include.
        var totalMs = ElapsedMs(startedAt);

        var searchEventId = await RecordAsync(request, userId, role, groups, totalMs);

        var response = new AgentAssistResponse
        {
            Groups = groups,
            Pitch = string.IsNullOrWhiteSpace(ai?.Pitch) ? null : ai.Pitch,
            PitchStatus = StatusOf(ai),
            Citations = ai is null
                ? []
                : ai.Citations.Select(citation => new SalesAssistCitationDto
                {
                    CitationId = citation.CitationId,
                    DocumentTitle = citation.DocumentTitle,
                    SectionTitle = citation.SectionTitle,
                    DocType = citation.DocType,
                    ClaimScope = citation.ClaimScope,
                    Snippet = citation.Snippet
                }).ToList(),
            Warnings = QueryWarnings(ai),
            ClarificationQuestion = ai?.ClarificationQuestion,
            Intent = ai?.Intent,
            Abstained = ai?.Abstained ?? false,
            AiAvailable = ai is not null,
            DegradedReason = degradedReason,

            // **The five the agent adds, carried and never computed.** `StopReason` in particular:
            // a count of iterations does not say whether the last was the last one needed or the
            // one that ran out, and those are opposite claims about the answer being read.
            Partial = ai?.Partial ?? false,
            StopReason = ai?.StopReason ?? string.Empty,
            Iterations = ai?.Iterations ?? 0,
            ToolCallsUsed = ai?.ToolCallsUsed ?? 0,
            Trace = TraceOf(ai),
            AgentPromptVersion = ai?.AgentPromptVersion,

            Usage = isAdmin ? UsageOf(ai, aiMs, totalMs) : null,
            SearchEventId = searchEventId,
            PointOfSaleId = request.PointOfSaleId,
            CandidatesReturned = candidates,
            SurvivedHydration = survived,
            TraceId = _traceContext.CurrentTraceId
        };

        LogFunnel(request, response, aiMs, totalMs);

        return AgentAssistResult.Ok(response);
    }

    /// <summary>
    /// Checks that the caller may converse about this point of sale, and that it is usable at all.
    /// </summary>
    /// <remarks>
    /// <strong>Copied from the free-query route rather than hardened.</strong> Two sibling panels
    /// with two different authorisation rules break without any test failing, so the rule is the
    /// same one: the every-shop scope is open to operators and administrators alike — it discloses
    /// nothing a caller could not already read — and the boundary that is actually protected is the
    /// narrow one, that a caller cannot name a shop they are not assigned to.
    /// </remarks>
    private async Task<AgentAssistResult?> AuthoriseAsync(
        Guid? pointOfSaleId,
        Guid userId,
        bool isAdmin,
        CancellationToken cancellationToken)
    {
        if (pointOfSaleId is not { } named)
        {
            return null;
        }

        if (!await _repository.IsPointOfSaleActiveAsync(named, cancellationToken))
        {
            return AgentAssistResult.Unavailable();
        }

        if (isAdmin)
        {
            return null;
        }

        return await _userPointOfSaleService.HasAccessAsync(userId, named)
            ? null
            : AgentAssistResult.Forbidden();
    }

    /// <summary>
    /// The call, with every failure of the gateway turned into a reason to degrade.
    /// </summary>
    /// <remarks>
    /// The same partition and the same vocabulary the free-query route uses, because the screen
    /// already knows how to word each of them and a sixth word for the same situation would be a
    /// second thing to translate.
    ///
    /// <strong>A slow conversation must not open the circuit of a route that answers correctly.</strong>
    /// It does not, and not by care taken here: the agent rides a named client of its own with a
    /// circuit of its own, so the isolation is structural rather than a rule somebody remembers.
    /// </remarks>
    private async Task<(AiAssistAgentResponse? Response, string? DegradedReason)> CallAsync(
        AgentAssistRequest request,
        AiAgentAssistOptions options,
        Guid userId,
        string role,
        CancellationToken cancellationToken)
    {
        var traceId = _traceContext.CurrentTraceId;
        var scope = ScopeOf(request.PointOfSaleId, userId, role);

        try
        {
            var response = await _gateway.AssistAgentAsync(
                new AiAssistAgentRequest
                {
                    // **No point of sale in the body**: the contract accepts one and ignores it, and
                    // the scope travels in the token the gateway builds from `scope`.
                    Turns = request.Turns
                        .Select(turn => new AiAgentTurn { Role = turn.Role, Text = turn.Text })
                        .ToList(),
                    TopK = options.CandidateWindow
                },
                scope,
                cancellationToken);

            return (response, null);
        }
        catch (AiGatewayConfigurationException exception)
        {
            _logger.LogError(exception,
                "Agent turn degraded: the AI service rejected the gateway credentials. TraceId={TraceId}", traceId);
            return (null, "credential_rejected");
        }
        catch (AiNotImplementedException exception)
        {
            _logger.LogError(exception,
                "Agent turn degraded: the route is not implemented on the AI service. TraceId={TraceId}", traceId);
            return (null, "not_implemented");
        }
        catch (AiRequestRejectedException exception)
        {
            // Normally unreachable: the validator refuses an over-long transcript before the call.
            // Kept because the layer is also a callable and the two paths must answer the same way.
            _logger.LogWarning(exception,
                "Agent turn degraded: the AI service refused the transcript. TraceId={TraceId}", traceId);
            return (null, "not_indexed");
        }
        catch (AiUnavailableException exception)
        {
            _logger.LogWarning(exception,
                "Agent turn degraded: the AI service is unavailable. TraceId={TraceId}", traceId);
            return (null, "ai_unavailable");
        }
        catch (AiGatewayException exception)
        {
            _logger.LogError(exception,
                "Agent turn degraded: unclassified gateway failure of type {FailureType}. TraceId={TraceId}",
                exception.GetType().Name, traceId);
            return (null, "unclassified");
        }
    }

    /// <summary>
    /// Hydrates every member of every group against the catalog, keeping the service's order and
    /// <strong>each group's provenance</strong>.
    /// </summary>
    /// <remarks>
    /// One query for every member of every group, not one per group. <strong>Substitute groups are
    /// hydrated on exactly the same terms as catalogue ones</strong>: a substitute is a piece of this
    /// catalogue like any other, and treating it differently would be the way to end up showing one
    /// without a price. What differs is only the label, and the label comes from
    /// <see cref="AgentAssistGroupDto.Origin"/>.
    ///
    /// A member the point of sale does not carry drops out, and a group left with no member drops out
    /// with it — including a substitute group, because an alternative nobody can sell here is not an
    /// alternative.
    /// </remarks>
    private async Task<List<AgentAssistGroupDto>> HydrateAsync(
        AiAssistAgentResponse ai,
        Guid? pointOfSaleId,
        int pageSize,
        CancellationToken cancellationToken)
    {
        var ids = new List<Guid>();
        foreach (var member in ai.Groups.SelectMany(group => group.Members))
        {
            if (Guid.TryParse(member.ProductId, out var id))
            {
                ids.Add(id);
            }
            else
            {
                _logger.LogWarning(
                    "Agent turn dropped a candidate whose product identifier is not a GUID. Sku={Sku} TraceId={TraceId}",
                    member.Sku,
                    _traceContext.CurrentTraceId);
            }
        }

        if (ids.Count == 0)
        {
            return [];
        }

        var rows = await _repository.HydrateAsync(ids, pointOfSaleId, cancellationToken);

        var byId = rows.ToDictionary(row => row.ProductId);
        var groups = new List<AgentAssistGroupDto>();

        foreach (var group in ai.Groups.Take(pageSize))
        {
            var members = new List<AssistedSearchResultDto>();

            foreach (var member in group.Members)
            {
                if (!Guid.TryParse(member.ProductId, out var id) || !byId.TryGetValue(id, out var row))
                {
                    continue;
                }

                members.Add(await _projector.ProjectAsync(row, new AiSearchResult
                {
                    ProductId = member.ProductId,
                    Sku = member.Sku,
                    Score = member.Score,
                    Materials = member.Materials,
                    MatchReasons = member.MatchReasons,
                    FamilyId = group.FamilyId,
                    VariantLabel = member.VariantLabel
                }));
            }

            if (members.Count > 0)
            {
                groups.Add(new AgentAssistGroupDto
                {
                    FamilyId = group.FamilyId,
                    FamilyLabel = group.FamilyLabel,
                    // Carried through untouched. Never derived from the group's position, which
                    // says nothing: the payload keeps the order the evidence arrived in.
                    Origin = group.Origin,
                    Members = members
                });
            }
        }

        return groups;
    }

    /// <summary>The trace as the screen shows it: steps, outcomes and cost, never arguments.</summary>
    private static List<AgentTraceIterationDto> TraceOf(AiAssistAgentResponse? ai) =>
        ai is null
            ? []
            : ai.Trace.Select(iteration => new AgentTraceIterationDto
            {
                Iteration = iteration.Iteration,
                Tools = iteration.Tools.Select(tool => new AgentTraceToolDto
                {
                    Tool = tool.Tool,
                    Ok = tool.Ok,
                    Cause = tool.Cause
                }).ToList(),
                PromptTokens = iteration.PromptTokens,
                CompletionTokens = iteration.CompletionTokens,
                TotalTokens = iteration.TotalTokens,
                ElapsedMs = iteration.ElapsedMs
            }).ToList();

    /// <summary>
    /// The warnings that describe <strong>the conversation</strong>, which are the only ones this
    /// screen may paint.
    /// </summary>
    /// <remarks>
    /// The same allow-list the free-query panel applies, and for the same reason: the AI service
    /// stacks two subjects into one array, and a warning about a piece describes the first member of
    /// the first group. Filtering by an allow-list rather than a deny-list keeps a code added later
    /// from leaking onto the screen by default.
    /// </remarks>
    private static List<string> QueryWarnings(AiAssistAgentResponse? ai) =>
        ai is null
            ? []
            : ai.Warnings.Where(QueryWarningCodes.Contains).ToList();

    /// <summary>Warning codes whose subject is the conversation rather than a piece.</summary>
    private static readonly HashSet<string> QueryWarningCodes =
    [
        "query_out_of_domain",
        "query_not_in_catalogue",
        "knowledge_not_covered",
        "filters_too_narrow"
    ];

    /// <summary>
    /// The state of the argument. The free-query route's rule, and for the same reason.
    /// </summary>
    /// <remarks>
    /// The agent's argument carries no placeholder — <c>assist/v6</c> forbids them for its task and
    /// a hard cause in the service's integrity gate enforces it — so there is no resolution step and
    /// therefore no <c>withheld_unresolved</c>. A version present with no text means the model wrote
    /// and the gate withheld; a version absent means nothing generated.
    /// </remarks>
    private static PitchStatus StatusOf(AiAssistAgentResponse? ai)
    {
        if (ai is null)
        {
            return PitchStatus.AiUnavailable;
        }

        if (ai.PromptVersion is null)
        {
            return PitchStatus.NotGenerated;
        }

        return string.IsNullOrWhiteSpace(ai.Pitch)
            ? PitchStatus.WithheldByAi
            : PitchStatus.Generated;
    }

    /// <summary>What the turn cost. Built only when the caller is an administrator.</summary>
    /// <remarks>
    /// <c>ProviderCalls</c> is the figure the free query has no use for and this route cannot do
    /// without: it is what makes the loop's ceiling observable from the same object a consumer reads,
    /// and the loop's ceiling is one of the things the project evaluates about an agent.
    /// </remarks>
    private static AgentAssistUsageDto? UsageOf(AiAssistAgentResponse? ai, int? aiMs, int totalMs) =>
        new()
        {
            Model = ai?.Usage.Model,
            PromptTokens = ai?.Usage.PromptTokens ?? 0,
            CompletionTokens = ai?.Usage.CompletionTokens ?? 0,
            TotalTokens = ai?.Usage.TotalTokens ?? 0,
            PromptVersion = ai?.PromptVersion,
            ProviderCalls = ai?.Usage.Calls ?? 0,
            AiMs = aiMs,
            TotalMs = totalMs
        };

    /// <summary>
    /// The scope that carries the shop into the service token, or its deliberate absence.
    /// </summary>
    /// <remarks>
    /// The every-shop scope omits the <c>pos_id</c> claim rather than filling it with a sentinel, and
    /// the service reads an absent claim as «do not apply the availability prefilter». On this route
    /// the absence costs one thing more: the availability label can then only say that no scope
    /// applies, so the loop never pivots to substitutes.
    /// </remarks>
    private static AiCallScope ScopeOf(Guid? pointOfSaleId, Guid userId, string role) =>
        pointOfSaleId is { } named
            ? AiCallScope.ForPointOfSale(userId, role, named)
            : AiCallScope.ForAllPointsOfSale(userId, role);

    /// <summary>
    /// Records the turn under the agent's own origin. Never throws: telemetry is expendable and a
    /// conversation is not.
    /// </summary>
    /// <remarks>
    /// <strong>The last operator turn is what is persisted as the query</strong>, which is the turn
    /// being answered. The rest of the transcript is not: it is what a customer said at a counter,
    /// and the retention limitation the semantic path already declares covers one query and not a
    /// conversation.
    ///
    /// <strong>A conversation spread over every shop is not recorded, and that is the inherited
    /// gap.</strong> <c>ProductSearchEvent.PointOfSaleId</c> is a required column with an index on
    /// it, so recording one would need an EF Core migration — which this change does not take — and
    /// writing a placeholder shop is what the specification forbids. Declared, as C40 declared it.
    /// </remarks>
    private async Task<Guid?> RecordAsync(
        AgentAssistRequest request,
        Guid userId,
        string role,
        List<AgentAssistGroupDto> groups,
        int totalMs)
    {
        if (request.PointOfSaleId is null)
        {
            return null;
        }

        // The rows the operator actually saw, flattened in the order the block paints them: group by
        // group and, inside each, member by member. That walk is the rank they perceived, which is
        // the only rank a selection can be measured against.
        var displayed = groups
            .SelectMany(group => group.Members)
            .Select(member => new AiSearchResult
            {
                ProductId = member.ProductId.ToString(),
                Sku = member.Sku,
                Score = member.Score ?? 0,
                MatchReasons = member.MatchReasons,
                FamilyId = member.FamilyId,
                VariantLabel = member.VariantLabel
            })
            .ToList();

        var answered = request.Turns
            .LastOrDefault(turn => turn.Role == AgentTranscriptCaps.OperatorRole)?.Text
            ?? string.Empty;

        try
        {
            return await _searchEventService.RecordSearchAsync(new RecordSearchRequest
            {
                Scope = ScopeOf(request.PointOfSaleId, userId, role),
                Query = answered,
                Filters = new AiSearchFilters(),
                DisplayedResults = displayed,
                // The fifth origin. What it buys is that «what did the operator get for the extra
                // cost of a conversation» is a query over this table rather than a demonstration.
                Origin = SearchOrigin.AssistedAgent,
                SearchSessionId = request.SearchSessionId,
                TraceId = _traceContext.CurrentTraceId,
                RetrievalMs = null,
                TotalMs = totalMs
            });
        }
        catch (Exception exception)
        {
            _logger.LogWarning(exception,
                "Agent turn served but telemetry could not persist. TraceId={TraceId}",
                _traceContext.CurrentTraceId);
            return null;
        }
    }

    private void LogFunnel(
        AgentAssistRequest request,
        AgentAssistResponse response,
        int? aiMs,
        int totalMs)
    {
        // Neither the transcript nor the argument. Lengths and counters are diagnostic without being
        // content, and the stop reason is what a cost review reads first.
        _logger.LogInformation(
            "stage=agent_assist trace_id={TraceId} pos_id={PointOfSaleId} turns={Turns} transcript_chars={TranscriptChars} intent={Intent} ai_available={AiAvailable} degraded_reason={DegradedReason} pitch_status={PitchStatus} pitch_len={PitchLength} groups={Groups} survived={Survived} citations={Citations} warnings={Warnings} abstained={Abstained} partial={Partial} stop_reason={StopReason} iterations={Iterations} tool_calls={ToolCalls} ai_ms={AiMs} total_ms={TotalMs} prompt_version={PromptVersion} agent_prompt_version={AgentPromptVersion}",
            response.TraceId,
            request.PointOfSaleId,
            request.Turns.Count,
            request.Turns.Sum(turn => turn.Text?.Length ?? 0),
            response.Intent,
            response.AiAvailable,
            response.DegradedReason,
            response.PitchStatus,
            response.Pitch?.Length ?? 0,
            response.Groups.Count,
            response.SurvivedHydration,
            response.Citations.Count,
            string.Join(",", response.Warnings),
            response.Abstained,
            response.Partial,
            response.StopReason,
            response.Iterations,
            response.ToolCallsUsed,
            aiMs,
            totalMs,
            response.Usage?.PromptVersion,
            response.AgentPromptVersion);
    }

    private int ElapsedMs(long startedAt) =>
        (int)_timeProvider.GetElapsedTime(startedAt).TotalMilliseconds;
}
