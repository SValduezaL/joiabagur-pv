using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Domain.Interfaces.Repositories;
using JoiabagurPV.Domain.Interfaces.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace JoiabagurPV.Application.Services;

/// <summary>
/// Warning codes the sale card computes on this side, and the one it adjusts.
/// </summary>
public static class SalesAssistWarningCodes
{
    /// <summary>Emitted by the AI service; kept only while two or more members survive hydration.</summary>
    public const string FamilyHasVariants = "family_has_variants";

    /// <summary>The anchored product has between one unit and the configured threshold.</summary>
    public const string StockCritical = "stock_critical";

    /// <summary>Another member of the hydrated group is carried with no units.</summary>
    public const string FamilyMembersOutOfStock = "family_members_out_of_stock";
}

/// <summary>
/// Orchestrates one sale assistance: scope, product check, switch, the AI call, hydration of the
/// group, the warnings this side owns, the placeholders, degradation and telemetry.
/// </summary>
/// <remarks>
/// The one-sentence rule of §6.2 applied where it shows most: the AI service computes likeness
/// and writes; this side computes numbers and decides. Which members of the family exist in this
/// shop, how many units there are, whether stock is critical, and the price the argument is
/// written with all come from here.
/// </remarks>
public class SalesAssistService : ISalesAssistService
{
    private readonly IAiGatewayClient _gateway;
    private readonly IAssistedSearchRepository _repository;
    private readonly IProductFamilyRepository _families;
    private readonly IUserPointOfSaleService _userPointOfSaleService;
    private readonly IFileStorageService _fileStorage;
    private readonly ITraceContextAccessor _traceContext;
    private readonly IOptionsMonitor<AiSalesAssistOptions> _options;
    private readonly TimeProvider _timeProvider;
    private readonly ILogger<SalesAssistService> _logger;

    public SalesAssistService(
        IAiGatewayClient gateway,
        IAssistedSearchRepository repository,
        IProductFamilyRepository families,
        IUserPointOfSaleService userPointOfSaleService,
        IFileStorageService fileStorage,
        ITraceContextAccessor traceContext,
        IOptionsMonitor<AiSalesAssistOptions> options,
        TimeProvider timeProvider,
        ILogger<SalesAssistService> logger)
    {
        _gateway = gateway;
        _repository = repository;
        _families = families;
        _userPointOfSaleService = userPointOfSaleService;
        _fileStorage = fileStorage;
        _traceContext = traceContext;
        _options = options;
        _timeProvider = timeProvider;
        _logger = logger;
    }

    /// <inheritdoc/>
    public async Task<SalesAssistResult> AssistAsync(
        Guid productId,
        SalesAssistRequest request,
        Guid userId,
        string role,
        bool isAdmin,
        CancellationToken cancellationToken = default)
    {
        var startedAt = _timeProvider.GetTimestamp();
        var options = _options.CurrentValue;
        var pointOfSaleId = request.PointOfSaleId;

        // Before any call: a request this side is about to refuse must not cost a paid one.
        var (access, anchor) = await SalesCardAccess.ResolveAsync(
            _repository, _userPointOfSaleService, productId, pointOfSaleId, userId, isAdmin, cancellationToken);

        if (access != SalesCardAccessOutcome.Success)
        {
            return SalesAssistResult.Refused(access);
        }

        var question = string.IsNullOrWhiteSpace(request.Question) ? null : request.Question.Trim();

        if (question is not null)
        {
            // Written about a customer. Debug only, like the search query of C15.
            _logger.LogDebug(
                "stage=sales_assist_question trace_id={TraceId} pos_id={PointOfSaleId} product_id={ProductId} question={Question}",
                _traceContext.CurrentTraceId, pointOfSaleId, productId, question);
        }

        AiAssistSaleResponse? ai = null;
        string? degradedReason = null;
        int? aiMs = null;

        if (!options.IsEnabledFor(pointOfSaleId))
        {
            degradedReason = "switched_off";
        }
        else
        {
            var aiStartedAt = _timeProvider.GetTimestamp();
            (ai, degradedReason) = await CallAsync(productId, question, userId, role, pointOfSaleId, cancellationToken);
            aiMs = ElapsedMs(aiStartedAt);
        }

        var outcome = ai is null
            ? await DegradedAsync(productId, pointOfSaleId, anchor!, options, cancellationToken)
            : await ServedAsync(ai, productId, pointOfSaleId, question, anchor!, options, cancellationToken);

        // Assigned before the log line is written, and the log line reads it back from here. The
        // requirement is that the screen and the log cannot disagree for one trace; keeping a
        // single value rather than two that travel side by side is what makes that structural.
        outcome.Response.DegradedReason = degradedReason;

        LogOutcome(outcome, ai, productId, pointOfSaleId, question, aiMs, ElapsedMs(startedAt));

        return SalesAssistResult.Ok(outcome.Response);
    }

    /// <summary>
    /// The call, with every failure of the gateway turned into a reason to degrade. Never throws
    /// because of the AI: the card does not break when the AI does.
    /// </summary>
    private async Task<(AiAssistSaleResponse? Response, string? DegradedReason)> CallAsync(
        Guid productId,
        string? question,
        Guid userId,
        string role,
        Guid pointOfSaleId,
        CancellationToken cancellationToken)
    {
        // The scope carries the point of sale into the service token. It comes from the validated
        // request, never from anything the AI service is sent in the body.
        var scope = AiCallScope.ForPointOfSale(userId, role, pointOfSaleId);
        var traceId = _traceContext.CurrentTraceId;

        try
        {
            var response = await _gateway.AssistSaleAsync(
                new AiAssistSaleRequest { ProductId = productId.ToString(), Query = question },
                scope,
                cancellationToken);

            return (response, null);
        }
        catch (AiGatewayConfigurationException exception)
        {
            // Error, not warning: the card still renders, which is exactly why a wrong secret
            // would otherwise sit unnoticed behind a screen that looks fine.
            _logger.LogError(exception,
                "Sale assistance degraded: the AI service rejected the gateway credentials. TraceId={TraceId}", traceId);
            return (null, "credential_rejected");
        }
        catch (AiNotImplementedException exception)
        {
            _logger.LogError(exception,
                "Sale assistance degraded: the route is not implemented on the AI service. TraceId={TraceId}", traceId);
            return (null, "not_implemented");
        }
        catch (AiRequestRejectedException exception)
        {
            // Not an outage: a product created after the last synchronisation, a state the next
            // one fixes by itself. Told apart in the log and, since C40, in the body too: it
            // travels as DegradedReason so the screen can say "this piece is not ready yet"
            // instead of "the assistant is down". The pitch still degrades identically — the
            // distinction is in why, not in what the card can offer.
            _logger.LogWarning(exception,
                "Sale assistance degraded: reason=product_not_indexed, the AI service cannot process product {ProductId}. TraceId={TraceId}",
                productId, traceId);
            return (null, "product_not_indexed");
        }
        catch (AiUnavailableException exception)
        {
            _logger.LogWarning(exception,
                "Sale assistance degraded: the AI service is unavailable. TraceId={TraceId}", traceId);
            return (null, "ai_unavailable");
        }
        catch (AiGatewayException exception)
        {
            // Final clause over the abstract base, so "the card never breaks because of the AI"
            // survives the day somebody adds a fifth failure type.
            _logger.LogError(exception,
                "Sale assistance degraded: unclassified gateway failure of type {FailureType}. TraceId={TraceId}",
                exception.GetType().Name, traceId);
            return (null, "unclassified");
        }
    }

    /// <summary>
    /// The served path: the AI service's group, hydrated, with the warnings adjusted to this shop
    /// and the argument resolved against the anchored product.
    /// </summary>
    private async Task<Composition> ServedAsync(
        AiAssistSaleResponse ai,
        Guid productId,
        Guid pointOfSaleId,
        string? question,
        AssistedSearchRow anchor,
        AiSalesAssistOptions options,
        CancellationToken cancellationToken)
    {
        var membersReturned = ai.Groups.Sum(group => group.Members.Count);

        // One set-based hydration for every member of every group; the anchor check already ran
        // one of its own. Never one query per member.
        var ids = new List<Guid>(membersReturned);
        foreach (var member in ai.Groups.SelectMany(group => group.Members))
        {
            if (Guid.TryParse(member.ProductId, out var id))
            {
                ids.Add(id);
            }
            else
            {
                _logger.LogWarning(
                    "Sale assistance dropped a member whose product identifier is not a GUID. Sku={Sku} TraceId={TraceId}",
                    member.Sku, _traceContext.CurrentTraceId);
            }
        }

        var rows = ids.Count == 0
            ? []
            : await _repository.HydrateAsync(ids.Distinct().ToList(), pointOfSaleId, cancellationToken);

        var byId = rows.ToDictionary(row => row.ProductId);

        var groups = new List<SalesAssistGroupDto>(ai.Groups.Count);
        foreach (var aiGroup in ai.Groups)
        {
            var members = new List<SalesAssistMemberDto>(aiGroup.Members.Count);

            // The order is the AI service's, and the surviving members are placed back into it.
            // A member the shop does not carry, or no longer carries actively, is dropped here.
            foreach (var candidate in aiGroup.Members)
            {
                if (!Guid.TryParse(candidate.ProductId, out var id) || !byId.TryGetValue(id, out var row))
                {
                    continue;
                }

                if (!string.Equals(candidate.Sku, row.Sku, StringComparison.Ordinal))
                {
                    _logger.LogWarning(
                        "Sale assistance found index drift: the index reports SKU {IndexedSku} for product {ProductId}, the catalog holds {CatalogSku}. TraceId={TraceId}",
                        candidate.Sku, row.ProductId, row.Sku, _traceContext.CurrentTraceId);
                }

                members.Add(await ToMemberAsync(
                    row, candidate.VariantLabel, candidate.Materials, candidate.MatchReasons, productId));
            }

            if (members.Count > 0)
            {
                groups.Add(new SalesAssistGroupDto
                {
                    FamilyId = aiGroup.FamilyId,
                    FamilyLabel = aiGroup.FamilyLabel,
                    Members = members
                });
            }
        }

        var anchorGroup = groups.FirstOrDefault(group => group.Members.Any(member => member.IsAnchor));
        if (anchorGroup is null)
        {
            // Unreachable by the contract — the anchored modes group around the anchored product —
            // and handled all the same, because a card without its own piece is the one thing the
            // operator cannot work around. The piece goes first, on its own.
            _logger.LogWarning(
                "Sale assistance: the AI response carried no group with the anchored product {ProductId}; serving it alone. TraceId={TraceId}",
                productId, _traceContext.CurrentTraceId);

            anchorGroup = new SalesAssistGroupDto
            {
                Members = [await ToMemberAsync(byId.GetValueOrDefault(productId) ?? anchor, null, [], [], productId)]
            };
            groups.Insert(0, anchorGroup);
        }

        var anchorMember = anchorGroup.Members.Single(member => member.IsAnchor);

        // The AI service's codes first, minus any stock code — those are this side's alone — and
        // minus the variants warning when fewer than two members survive. It is only ever removed
        // on this path, never added: the family the index knows is the AI's call.
        var warnings = ai.Warnings
            .Where(code => code is not SalesAssistWarningCodes.StockCritical
                                and not SalesAssistWarningCodes.FamilyMembersOutOfStock)
            .ToList();

        if (anchorGroup.Members.Count < 2)
        {
            warnings.RemoveAll(code => code == SalesAssistWarningCodes.FamilyHasVariants);
        }

        AppendStockWarnings(warnings, anchorGroup, anchorMember, options);

        var (pitchStatus, pitch) = DecidePitch(ai, question, anchorMember);

        return new Composition(
            new SalesAssistResponse
            {
                AiAvailable = true,
                PointOfSaleId = pointOfSaleId,
                ProductId = productId,
                Intent = ai.Intent,
                Groups = groups,
                Pitch = pitch,
                PitchStatus = pitchStatus,
                // As the AI service declared them, the claim scope included. When this side
                // withholds the argument they stay the ones that argument used: the ones that
                // grounded the answer but not the argument cannot be reconstructed from here.
                Citations = ai.Citations.Select(citation => new SalesAssistCitationDto
                {
                    CitationId = citation.CitationId,
                    DocumentTitle = citation.DocumentTitle,
                    SectionTitle = citation.SectionTitle,
                    DocType = citation.DocType,
                    ClaimScope = citation.ClaimScope,
                    Snippet = citation.Snippet
                }).ToList(),
                Warnings = warnings,
                ClarificationQuestion = ai.ClarificationQuestion,
                PromptVersion = ai.PromptVersion,
                TraceId = _traceContext.CurrentTraceId
            },
            membersReturned);
    }

    /// <summary>
    /// The state of the argument, decided in the order of the design (D6); the first that applies
    /// wins. The argument is present only when <see cref="PitchStatus.Generated"/>.
    /// </summary>
    private static (PitchStatus Status, string? Pitch) DecidePitch(
        AiAssistSaleResponse ai,
        string? question,
        SalesAssistMemberDto anchor)
    {
        if (ai.PromptVersion is null)
        {
            return (PitchStatus.NotGenerated, null);
        }

        if (string.IsNullOrWhiteSpace(ai.Pitch))
        {
            return (PitchStatus.WithheldByAi, null);
        }

        // Without a question the argument is a sales argument, written by a model that does not
        // know the stock — «disponible por {{price}}» in 147 of 213. For a piece this shop cannot
        // sell today it argues for the sale the card is about to replace with substitutes. With a
        // question, the answer holds whether or not there are units, and the 0 is resolved.
        if (question is null && anchor.QuantityAtPointOfSale == 0)
        {
            return (PitchStatus.WithheldOutOfStock, null);
        }

        var resolution = PitchPlaceholderResolver.Resolve(
            ai.Pitch, new PitchAnchor(anchor.Price, anchor.QuantityAtPointOfSale));

        return resolution.IsResolved
            ? (PitchStatus.Generated, resolution.Text)
            : (PitchStatus.WithheldUnresolved, null);
    }

    /// <summary>
    /// The degraded card: the anchored product and the members of its family this shop carries,
    /// read from this side's own family records, with the stock and variants warnings computed
    /// here. No argument and no citations.
    /// </summary>
    /// <remarks>
    /// Confirming the variant before a sale is business logic, not AI, and the families are this
    /// side's (§6.2). It costs one query and reuses the hydration.
    /// </remarks>
    private async Task<Composition> DegradedAsync(
        Guid productId,
        Guid pointOfSaleId,
        AssistedSearchRow anchor,
        AiSalesAssistOptions options,
        CancellationToken cancellationToken)
    {
        var family = await _families.GetByProductIdAsync(productId);

        var declared = family?.Members
            .OrderBy(member => member.SortOrder)
            .Select(member => (member.ProductId, member.VariantLabel))
            .ToList() ?? [];

        IReadOnlyList<AssistedSearchRow> rows = declared.Count == 0
            ? [anchor]
            : await _repository.HydrateAsync(
                declared.Select(member => member.ProductId).ToList(), pointOfSaleId, cancellationToken);

        var byId = rows.ToDictionary(row => row.ProductId);
        var members = new List<SalesAssistMemberDto>(declared.Count);

        foreach (var (memberId, variantLabel) in declared)
        {
            if (byId.TryGetValue(memberId, out var row))
            {
                members.Add(await ToMemberAsync(row, variantLabel, [], [], productId));
            }
        }

        if (!members.Any(member => member.IsAnchor))
        {
            members.Insert(0, await ToMemberAsync(byId.GetValueOrDefault(productId) ?? anchor, null, [], [], productId));
        }

        var group = new SalesAssistGroupDto
        {
            FamilyId = family?.Id.ToString(),
            FamilyLabel = family?.Name,
            Members = members
        };

        // On this path the backend is the authority on the family, so the variants warning is
        // computed here — and may be added, unlike on the served path.
        var warnings = new List<string>();
        if (family is not null && members.Count >= 2)
        {
            warnings.Add(SalesAssistWarningCodes.FamilyHasVariants);
        }

        AppendStockWarnings(warnings, group, members.Single(member => member.IsAnchor), options);

        return new Composition(
            new SalesAssistResponse
            {
                AiAvailable = false,
                PointOfSaleId = pointOfSaleId,
                ProductId = productId,
                Intent = null,
                Groups = [group],
                Pitch = null,
                PitchStatus = PitchStatus.AiUnavailable,
                Citations = [],
                Warnings = warnings,
                TraceId = _traceContext.CurrentTraceId
            },
            declared.Count);
    }

    /// <summary>
    /// The two stock warnings, from hydrated quantities only. Zero on the anchored product is a
    /// state of the member, not critical stock.
    /// </summary>
    private static void AppendStockWarnings(
        List<string> warnings,
        SalesAssistGroupDto group,
        SalesAssistMemberDto anchor,
        AiSalesAssistOptions options)
    {
        if (anchor.QuantityAtPointOfSale >= 1 && anchor.QuantityAtPointOfSale <= options.StockCriticalThreshold)
        {
            warnings.Add(SalesAssistWarningCodes.StockCritical);
        }

        if (group.Members.Any(member => !member.IsAnchor && member.QuantityAtPointOfSale == 0))
        {
            warnings.Add(SalesAssistWarningCodes.FamilyMembersOutOfStock);
        }
    }

    private async Task<SalesAssistMemberDto> ToMemberAsync(
        AssistedSearchRow row,
        string? variantLabel,
        List<string> materials,
        List<string> matchReasons,
        Guid anchorId) => new()
    {
        ProductId = row.ProductId,
        Sku = row.Sku,
        Name = row.Name,
        VariantLabel = variantLabel,
        Price = row.Price,
        // The row always carries a quantity here: the sale card is refused without a
        // point of sale, so the hydration that produced this row named one. Stated as a throw
        // rather than as a `?? 0`, because a zero would be a claim about stock and this is a
        // claim about the code.
        QuantityAtPointOfSale = row.Quantity
            ?? throw new InvalidOperationException(
                "A sale card hydrated without a point of sale. The card is refused without one."),
        HasStock = row.Quantity > 0,
        PrimaryPhotoUrl = row.PrimaryPhotoFileName is null
            ? null
            : await _fileStorage.GetUrlAsync(row.PrimaryPhotoFileName, "products"),
        CollectionName = row.CollectionName,
        Materials = materials,
        MatchReasons = matchReasons,
        IsAnchor = row.ProductId == anchorId
    };

    /// <summary>
    /// One line per request. The argument is NOT in it, at any level, resolved or not: resolved it
    /// carries the real price, which the placeholder mechanism exists to keep out of generated
    /// text. Its length is diagnostic without being content. Token usage is logged for cost and
    /// never exposed to the frontend.
    /// </summary>
    private void LogOutcome(
        Composition outcome,
        AiAssistSaleResponse? ai,
        Guid productId,
        Guid pointOfSaleId,
        string? question,
        int? aiMs,
        int totalMs)
    {
        var response = outcome.Response;

        _logger.LogInformation(
            "stage=sales_assist trace_id={TraceId} pos_id={PointOfSaleId} product_id={ProductId} mode={Mode} ai_available={AiAvailable} degraded_reason={DegradedReason} pitch_status={PitchStatus} pitch_len={PitchLength} citation_ids={CitationIds} warnings={Warnings} members_returned={MembersReturned} members_carried={MembersCarried} ai_ms={AiMs} total_ms={TotalMs} prompt_version={PromptVersion} model={Model} prompt_tokens={PromptTokens} completion_tokens={CompletionTokens}",
            response.TraceId,
            pointOfSaleId,
            productId,
            question is null ? "M2" : "M3",
            response.AiAvailable,
            response.DegradedReason,
            ToWire(response.PitchStatus),
            response.Pitch?.Length ?? 0,
            string.Join(",", response.Citations.Select(citation => citation.CitationId)),
            string.Join(",", response.Warnings),
            outcome.MembersReturned,
            response.Groups.Sum(group => group.Members.Count),
            aiMs,
            totalMs,
            ai?.PromptVersion,
            ai?.Usage.Model,
            ai?.Usage.PromptTokens,
            ai?.Usage.CompletionTokens);
    }

    /// <summary>The wire value of a state, so the log counts what the frontend receives.</summary>
    internal static string ToWire(PitchStatus status) => status switch
    {
        PitchStatus.AiUnavailable => "ai_unavailable",
        PitchStatus.NotGenerated => "not_generated",
        PitchStatus.WithheldByAi => "withheld_by_ai",
        PitchStatus.WithheldOutOfStock => "withheld_out_of_stock",
        PitchStatus.WithheldUnresolved => "withheld_unresolved",
        PitchStatus.Generated => "generated",
        _ => status.ToString()
    };

    private int ElapsedMs(long startedAt) =>
        (int)_timeProvider.GetElapsedTime(startedAt).TotalMilliseconds;

    /// <summary>
    /// The response, plus what the log needs and the frontend does not: how many members the
    /// source proposed — the AI service's groups, or the catalog's family on the degraded path.
    /// </summary>
    private sealed record Composition(SalesAssistResponse Response, int MembersReturned);
}
