using System.Globalization;
using System.Text.Json;
using FluentAssertions;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
using JoiabagurPV.Domain.Entities;
using JoiabagurPV.Domain.Interfaces.Repositories;
using JoiabagurPV.Domain.Interfaces.Services;
using JoiabagurPV.Tests.TestHelpers;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.Time.Testing;
using Moq;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// Unit tests for the sale assistance orchestrator. No AI service and no database: the gateway,
/// the repositories and the file store are doubles.
/// </summary>
/// <remarks>
/// Hydration is simulated as the repository behaves: it returns, among the requested identifiers,
/// the ones this point of sale carries — so "the shop does not carry it" is the absence of a row
/// in <see cref="_carried"/>, exactly as in the database.
/// </remarks>
public class SalesAssistServiceTests
{
    private static readonly CultureInfo Spanish = CultureInfo.GetCultureInfo("es-ES");
    private static readonly Guid UserId = Guid.Parse("11111111-1111-1111-1111-111111111111");
    private static readonly Guid PosId = Guid.Parse("22222222-2222-2222-2222-222222222222");

    private static readonly Guid Anchor = Guid.Parse("aaaaaaaa-0000-0000-0000-000000000001");
    private static readonly Guid Sibling = Guid.Parse("aaaaaaaa-0000-0000-0000-000000000002");
    private static readonly Guid NotCarried = Guid.Parse("aaaaaaaa-0000-0000-0000-000000000003");

    private const string Template = "Pendientes de plata, disponibles por {{price}} y tenemos {{stock}} en tienda.";

    private readonly Mock<IAiGatewayClient> _gateway = new();
    private readonly Mock<IAssistedSearchRepository> _repository = new();
    private readonly Mock<IProductFamilyRepository> _families = new();
    private readonly Mock<IUserPointOfSaleService> _userPointOfSale = new();
    private readonly Mock<IFileStorageService> _fileStorage = new();
    private readonly Mock<ITraceContextAccessor> _traceContext = new();
    private readonly RecordingLoggerProvider _logs = new();
    private readonly List<AssistedSearchRow> _carried = [];
    private readonly List<IReadOnlyList<Guid>> _hydrations = [];

    private readonly AiSalesAssistOptions _options = new() { EnabledByDefault = true };

    public SalesAssistServiceTests()
    {
        _traceContext.SetupGet(t => t.CurrentTraceId).Returns("trace-assist-1");

        _repository
            .Setup(r => r.IsPointOfSaleActiveAsync(PosId, It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        _repository
            .Setup(r => r.HydrateAsync(It.IsAny<IReadOnlyList<Guid>>(), PosId, It.IsAny<CancellationToken>()))
            .ReturnsAsync((IReadOnlyList<Guid> ids, Guid _, CancellationToken _) =>
            {
                _hydrations.Add(ids);
                return _carried.Where(row => ids.Contains(row.ProductId)).ToList();
            });

        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, PosId)).ReturnsAsync(true);

        _fileStorage
            .Setup(f => f.GetUrlAsync(It.IsAny<string>(), It.IsAny<string>()))
            .ReturnsAsync((string file, string? _) => "https://files.test/" + file);

        Carry(Anchor, "ERIZO-M", price: 39.90m, quantity: 3);
    }

    // ---------------------------------------------------------------- scope, before any call

    [Fact]
    public async Task AssistAsync_AsOperatorOfAnotherPos_IsForbiddenWithoutCallingAi()
    {
        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, PosId)).ReturnsAsync(false);

        var result = await AssistAsync();

        result.Outcome.Should().Be(SalesCardAccessOutcome.PointOfSaleForbidden);
        VerifyNoAiCall();
    }

    [Fact]
    public async Task AssistAsync_AnchorNotCarriedAtPos_IsNotFoundWithoutCallingAi()
    {
        _carried.Clear();

        var result = await AssistAsync();

        result.Outcome.Should().Be(SalesCardAccessOutcome.ProductNotFound);
        VerifyNoAiCall();
    }

    [Fact]
    public async Task AssistAsync_WhenPointOfSaleInactive_IsRefusedForAdministratorsToo()
    {
        _repository.Setup(r => r.IsPointOfSaleActiveAsync(PosId, It.IsAny<CancellationToken>())).ReturnsAsync(false);

        var result = await AssistAsync(isAdmin: true);

        result.Outcome.Should().Be(SalesCardAccessOutcome.PointOfSaleUnavailable);
        VerifyNoAiCall();
    }

    [Fact]
    public async Task AssistAsync_AdministratorWithoutAssignment_IsServed()
    {
        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, PosId)).ReturnsAsync(false);
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M")));

        var result = await AssistAsync(isAdmin: true);

        result.Outcome.Should().Be(SalesCardAccessOutcome.Success);
    }

    // ---------------------------------------------------------------- the call

    [Fact]
    public async Task SalesAssist_SendsThePointOfSaleThroughTheScope_NotTheBody()
    {
        AiCallScope? scope = null;
        AiAssistSaleRequest? sent = null;
        _gateway
            .Setup(g => g.AssistSaleAsync(It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .Callback<AiAssistSaleRequest, AiCallScope, CancellationToken>((r, s, _) => { sent = r; scope = s; })
            .ReturnsAsync(Ai(Member(Anchor, "ERIZO-M")));

        await AssistAsync(question: "  ¿se puede mojar?  ");

        scope!.PointOfSaleId.Should().Be(PosId);
        scope.UserId.Should().Be(UserId);
        sent!.ProductId.Should().Be(Anchor.ToString());
        sent.Query.Should().Be("¿se puede mojar?", "the question is trimmed before it leaves");

        JsonSerializer.Serialize(sent, AiGatewaySerialization.Options).Should().NotContain("pos_id");
    }

    [Fact]
    public async Task SalesAssist_WithoutQuestion_SendsANullQuery()
    {
        AiAssistSaleRequest? sent = null;
        _gateway
            .Setup(g => g.AssistSaleAsync(It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .Callback<AiAssistSaleRequest, AiCallScope, CancellationToken>((r, _, _) => sent = r)
            .ReturnsAsync(Ai(Member(Anchor, "ERIZO-M")));

        await AssistAsync();

        sent!.Query.Should().BeNull("a piece with no question is M2");
    }

    // ---------------------------------------------------------------- hydration of the group

    [Fact]
    public async Task SalesAssist_DropsMembersThePointOfSaleDoesNotCarry()
    {
        Carry(Sibling, "ERIZO-S", quantity: 4);
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M"), Member(NotCarried, "ERIZO-L"), Member(Sibling, "ERIZO-S")));

        var response = (await AssistAsync()).Response!;

        response.Groups.Should().ContainSingle()
            .Which.Members.Select(m => m.ProductId).Should().Equal(Anchor, Sibling);
    }

    [Fact]
    public async Task SalesAssist_KeepsTheOrderOfTheAiService()
    {
        Carry(Sibling, "ERIZO-S", quantity: 4);
        var third = Guid.NewGuid();
        Carry(third, "ERIZO-XL", quantity: 1);

        // The anchor is NOT first on purpose: this side does not reorder, it marks.
        GatewayReturns(Ai(Member(Sibling, "ERIZO-S"), Member(third, "ERIZO-XL"), Member(Anchor, "ERIZO-M")));

        var members = (await AssistAsync()).Response!.Groups.Single().Members;

        members.Select(m => m.ProductId).Should().Equal(Sibling, third, Anchor);
        members.Should().ContainSingle(m => m.IsAnchor).Which.ProductId.Should().Be(Anchor);
    }

    /// <summary>
    /// Price and quantity of every member come from the catalog of that shop; the resolved argument
    /// carries the anchored product's, formatted as the design says.
    /// </summary>
    [Fact]
    public async Task SalesAssist_ReplacesPlaceholdersWithRealValues()
    {
        Carry(Sibling, "ERIZO-S", price: 44.00m, quantity: 7);
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M"), Member(Sibling, "ERIZO-S")));

        var response = (await AssistAsync()).Response!;

        var anchor = response.Groups.Single().Members.Single(m => m.IsAnchor);
        anchor.Price.Should().Be(39.90m);
        anchor.QuantityAtPointOfSale.Should().Be(3);
        anchor.HasStock.Should().BeTrue();
        response.Groups.Single().Members.Single(m => !m.IsAnchor).Price.Should().Be(44.00m);

        response.PitchStatus.Should().Be(PitchStatus.Generated);
        response.Pitch.Should().Be(
            $"Pendientes de plata, disponibles por {39.90m.ToString("C2", Spanish)} y tenemos 3 en tienda.");
    }

    [Fact]
    public async Task SalesAssist_HydratesTheGroupInASingleQuery()
    {
        var members = Enumerable.Range(0, 8).Select(_ => Guid.NewGuid()).ToList();
        foreach (var id in members)
        {
            Carry(id, "SKU-" + id.ToString()[..4], quantity: 1);
        }

        GatewayReturns(Ai([Member(Anchor, "ERIZO-M"), .. members.Select(id => Member(id, "SKU-" + id.ToString()[..4]))]));

        await AssistAsync();

        _hydrations.Should().HaveCount(2, "one query checks the anchor, one hydrates the whole group");
        _hydrations[1].Should().HaveCount(9);
    }

    [Fact]
    public async Task SalesAssist_CatalogSkuWins_AndTheDriftIsLogged()
    {
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M-OLD")));

        var response = (await AssistAsync()).Response!;

        response.Groups.Single().Members.Single().Sku.Should().Be("ERIZO-M");
        _logs.Entries.Should().Contain(e => e.Message.Contains("index drift"));
    }

    [Fact]
    public async Task SalesAssist_DropsAMemberWhoseIdentifierIsNotAGuid()
    {
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M"), new AiAssistGroupMember { ProductId = "not-a-guid", Sku = "X" }));

        var response = (await AssistAsync()).Response!;

        response.Groups.Single().Members.Should().ContainSingle();
        _logs.Entries.Should().Contain(e => e.Level == LogLevel.Warning && e.Message.Contains("not a GUID"));
    }

    [Fact]
    public async Task SalesAssist_WhenTheAiGroupLacksTheAnchor_ServesTheAnchorAlone()
    {
        Carry(Sibling, "ERIZO-S", quantity: 2);
        GatewayReturns(Ai(Member(Sibling, "ERIZO-S")));

        var response = (await AssistAsync()).Response!;

        response.Groups[0].Members.Should().ContainSingle().Which.IsAnchor.Should().BeTrue();
    }

    // ---------------------------------------------------------------- warnings

    [Fact]
    public async Task SalesAssist_FamilyHasVariantsDroppedWhenOneMemberSurvives()
    {
        GatewayReturns(Ai(
            [Member(Anchor, "ERIZO-M"), Member(NotCarried, "ERIZO-L"), Member(Guid.NewGuid(), "ERIZO-XL")],
            warnings: ["family_has_variants"]));

        var response = (await AssistAsync()).Response!;

        response.Groups.Single().Members.Should().ContainSingle();
        response.Warnings.Should().NotContain("family_has_variants",
            "asking the operator to choose among one option is the failure the nullable family removed");
    }

    [Fact]
    public async Task SalesAssist_FamilyHasVariantsKeptWhenTwoMembersSurvive()
    {
        Carry(Sibling, "ERIZO-S", quantity: 5);
        GatewayReturns(Ai(
            [Member(Anchor, "ERIZO-M"), Member(Sibling, "ERIZO-S"), Member(NotCarried, "ERIZO-L")],
            warnings: ["family_has_variants"]));

        var response = (await AssistAsync()).Response!;

        response.Warnings.Should().Contain("family_has_variants");
    }

    [Fact]
    public async Task SalesAssist_FamilyHasVariantsNeverAddedOnTheServedPath()
    {
        Carry(Sibling, "ERIZO-S", quantity: 5);
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M"), Member(Sibling, "ERIZO-S")], warnings: []));

        var response = (await AssistAsync()).Response!;

        response.Warnings.Should().NotContain("family_has_variants", "on this path it may only be removed");
    }

    /// <summary>
    /// Both stock warnings come from hydrated quantities. The AI response carries none — and one it
    /// did carry would be dropped, because a stock figure is never the AI's to state.
    /// </summary>
    [Fact]
    public async Task SalesAssist_StockWarningsComputedAfterHydration_NotTakenFromPython()
    {
        _carried.Clear();
        Carry(Anchor, "ERIZO-M", quantity: 2);
        Carry(Sibling, "ERIZO-S", quantity: 0);
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M"), Member(Sibling, "ERIZO-S"), Member(NotCarried, "ERIZO-L")],
            warnings: ["family_has_variants"]));

        var response = (await AssistAsync()).Response!;

        response.Warnings.Should().Equal("family_has_variants", "stock_critical", "family_members_out_of_stock");
    }

    [Fact]
    public async Task SalesAssist_StockCodesInTheAiResponse_AreNotTakenAsTheirOwn()
    {
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], warnings: ["stock_critical", "family_members_out_of_stock"]));

        var response = (await AssistAsync()).Response!;

        response.Warnings.Should().BeEmpty("three units is not critical and there is no other member");
    }

    [Fact]
    public async Task SalesAssist_ZeroStock_IsNotCriticalStock()
    {
        _carried.Clear();
        Carry(Anchor, "ERIZO-M", quantity: 0);
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M")));

        var response = (await AssistAsync(question: "¿es plata de ley?")).Response!;

        response.Warnings.Should().NotContain("stock_critical");
        response.Groups.Single().Members.Single().HasStock.Should().BeFalse();
    }

    [Theory]
    [InlineData(1, true)]
    [InlineData(2, true)]
    [InlineData(3, false)]
    public async Task SalesAssist_CriticalStock_FollowsTheDefaultThreshold(int quantity, bool critical)
    {
        _carried.Clear();
        Carry(Anchor, "ERIZO-M", quantity: quantity);
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M")));

        var response = (await AssistAsync()).Response!;

        response.Warnings.Contains("stock_critical").Should().Be(critical);
    }

    [Fact]
    public async Task SalesAssist_UnknownWarningCode_IsPassedThrough()
    {
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], warnings: ["size_label_missing", "a_code_from_the_future"]));

        var response = (await AssistAsync()).Response!;

        response.Warnings.Should().Equal("size_label_missing", "a_code_from_the_future");
    }

    /// <summary>
    /// When the corpus does not cover the question, the AI service says so with a code rather than
    /// pretending to have answered. The card must receive that code untouched.
    /// </summary>
    [Fact]
    public async Task SalesAssist_KnowledgeNotCovered_IsPassedThrough()
    {
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], warnings: ["knowledge_not_covered"]));

        var response = (await AssistAsync(question: "¿Se puede llevar en la sauna?")).Response!;

        response.Warnings.Should().Contain("knowledge_not_covered");
        response.Citations.Should().BeEmpty();
    }

    // ---------------------------------------------------------------- the argument

    [Fact]
    public async Task SalesAssist_WhenPlaceholderUnresolved_WithholdsThePitchInsteadOfShippingTheRawTemplate()
    {
        const string raw = "Por {{precio}} la tienes hoy.";
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], pitch: raw, warnings: ["size_label_missing"],
            citations: [Citation("plata#cuidados", "general")]));

        var response = (await AssistAsync()).Response!;

        response.Pitch.Should().BeNull();
        response.PitchStatus.Should().Be(PitchStatus.WithheldUnresolved);
        response.Groups.Should().NotBeEmpty();
        response.Warnings.Should().Contain("size_label_missing");
        response.Citations.Should().ContainSingle();

        JsonSerializer.Serialize(response).Should().NotContain("{{precio}}").And.NotContain("la tienes hoy");
        _logs.Entries.Should().NotContain(e => e.Mentions("la tienes hoy"));
    }

    [Fact]
    public async Task SalesAssist_NoGenerationAndWithheldGeneration_AreToldApart()
    {
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], pitch: "", promptVersion: null));
        var notGenerated = (await AssistAsync()).Response!;

        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], pitch: "", promptVersion: "assist/v4"));
        var withheld = (await AssistAsync()).Response!;

        notGenerated.PitchStatus.Should().Be(PitchStatus.NotGenerated);
        withheld.PitchStatus.Should().Be(PitchStatus.WithheldByAi);
        notGenerated.Pitch.Should().BeNull();
        withheld.Pitch.Should().BeNull();
        notGenerated.AiAvailable.Should().BeTrue();
    }

    [Fact]
    public async Task SalesAssist_AnchorOutOfStock_WithholdsPitchWithoutQuestion_KeepsItWithQuestion()
    {
        _carried.Clear();
        Carry(Anchor, "ERIZO-M", price: 39.90m, quantity: 0);
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M")));

        var withoutQuestion = (await AssistAsync()).Response!;
        var withQuestion = (await AssistAsync(question: "¿se oscurece la plata?")).Response!;

        withoutQuestion.PitchStatus.Should().Be(PitchStatus.WithheldOutOfStock);
        withoutQuestion.Pitch.Should().BeNull();
        withoutQuestion.Groups.Single().Members.Single().HasStock.Should().BeFalse(
            "that is what the card turns into its substitutes block");

        withQuestion.PitchStatus.Should().Be(PitchStatus.Generated);
        withQuestion.Pitch.Should().Contain("tenemos 0 en tienda");
    }

    /// <summary>
    /// The order of the design: the out-of-stock rule is fourth, after the two AI states.
    /// </summary>
    [Fact]
    public async Task SalesAssist_WithheldByAi_WinsOverOutOfStock()
    {
        _carried.Clear();
        Carry(Anchor, "ERIZO-M", quantity: 0);
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], pitch: "", promptVersion: "assist/v4"));

        (await AssistAsync()).Response!.PitchStatus.Should().Be(PitchStatus.WithheldByAi);
    }

    /// <summary>
    /// The only pair of the design's order (D6) the rest of this class leaves undecided: rule 4,
    /// the sold-out anchor, comes before rule 5, the placeholder that would not resolve. Both
    /// withhold the argument, so only the state told apart distinguishes them — and the state is
    /// what C36 paints. Added by the independent verification, which swapped the two rules and
    /// watched all forty-two tests here stay green.
    /// </summary>
    [Fact]
    public async Task SalesAssist_OutOfStockAnchor_WinsOverAnUnresolvedPlaceholder()
    {
        _carried.Clear();
        Carry(Anchor, "ERIZO-M", quantity: 0);
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], pitch: "Por {{precio}} la tienes hoy."));

        var response = (await AssistAsync()).Response!;

        response.PitchStatus.Should().Be(PitchStatus.WithheldOutOfStock,
            "rule 4 precedes rule 5, and the first that applies wins");
        response.Pitch.Should().BeNull();
    }

    [Fact]
    public async Task SalesAssist_WithQuestion_ReturnsCitationsCarryingClaimScope()
    {
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], citations:
        [
            Citation("garantia#devoluciones", "establecimiento"),
            Citation("plata#cuidados", "general")
        ]));

        var response = (await AssistAsync(question: "¿la puedo devolver?")).Response!;

        response.Citations.Select(c => c.ClaimScope).Should().Equal("establecimiento", "general");
        response.Citations[0].DocumentTitle.Should().Be("Doc garantia#devoluciones");
        response.Citations[0].SectionTitle.Should().Be("Sección");
        response.Citations[0].DocType.Should().Be("politica");
        response.Citations[0].Snippet.Should().Be("Fragmento.");
    }

    // ---------------------------------------------------------------- degradation

    /// <summary>
    /// An open circuit, an exhausted budget, a server error: the card is served from the catalog.
    /// </summary>
    [Fact]
    public async Task SalesAssist_WhenAiUnavailable_ServesAnchorAndFamilyFromCatalog()
    {
        Carry(Sibling, "ERIZO-S", price: 44m, quantity: 0);
        FamilyOf(Anchor, (Sibling, "S"), (Anchor, "M"), (NotCarried, "L"));
        GatewayThrows(new AiUnavailableException("circuit open"));

        var response = (await AssistAsync()).Response!;

        response.AiAvailable.Should().BeFalse();
        response.PitchStatus.Should().Be(PitchStatus.AiUnavailable);
        response.Pitch.Should().BeNull();
        response.Citations.Should().BeEmpty();
        response.Intent.Should().BeNull();

        var group = response.Groups.Should().ContainSingle().Subject;
        group.FamilyLabel.Should().Be("Pendiente erizo");
        group.Members.Select(m => (m.ProductId, m.VariantLabel)).Should().Equal(
            [(Sibling, "S"), (Anchor, "M")], "family order from the catalog, only what the shop carries");
        group.Members.Single(m => m.IsAnchor).Price.Should().Be(39.90m);

        response.Warnings.Should().Equal("family_has_variants", "family_members_out_of_stock");
        _logs.Entries.Should().Contain(e => e.Level == LogLevel.Warning && e.Message.Contains("unavailable"));
    }

    [Fact]
    public async Task SalesAssist_WhenAiUnavailable_AndNoFamily_ServesTheAnchorAlone()
    {
        GatewayThrows(new AiUnavailableException("timeout"));

        var response = (await AssistAsync()).Response!;

        response.Groups.Single().FamilyId.Should().BeNull();
        response.Groups.Single().Members.Should().ContainSingle().Which.IsAnchor.Should().BeTrue();
        response.Warnings.Should().BeEmpty();
    }

    [Fact]
    public async Task SalesAssist_WhenCredentialRejected_DegradesAndLogsError()
    {
        GatewayThrows(new AiGatewayConfigurationException("401"));

        var response = (await AssistAsync()).Response!;

        response.AiAvailable.Should().BeFalse();
        _logs.At(LogLevel.Error).Should().Contain(e => e.Message.Contains("credentials"));
    }

    [Fact]
    public async Task SalesAssist_When422_DegradesAndLogsProductNotIndexed()
    {
        GatewayThrows(new AiRequestRejectedException(422, "not indexed"));

        var response = (await AssistAsync()).Response!;

        response.AiAvailable.Should().BeFalse();
        response.PitchStatus.Should().Be(PitchStatus.AiUnavailable);
        _logs.At(LogLevel.Warning).Should().Contain(e => e.Message.Contains("reason=product_not_indexed"));
        StageLine().Property("DegradedReason").Should().Be("product_not_indexed");
    }

    [Theory]
    [MemberData(nameof(GatewayFailures))]
    public async Task SalesAssist_AnyGatewayFailure_DegradesAndNeverThrows(AiGatewayException failure)
    {
        GatewayThrows(failure);

        var result = await AssistAsync();

        result.Outcome.Should().Be(SalesCardAccessOutcome.Success);
        result.Response!.AiAvailable.Should().BeFalse();
    }

    public static TheoryData<AiGatewayException> GatewayFailures => new()
    {
        new AiUnavailableException("timeout"),
        new AiNotImplementedException("501"),
        new AiGatewayConfigurationException("401"),
        new AiRequestRejectedException(422, "422")
    };

    // ---------------------------------------------------------------- the reason reaches the body

    [Fact]
    public async Task SalesAssist_WhenProductNotIndexed_ReportsThatReason()
    {
        GatewayThrows(new AiRequestRejectedException(422, "not indexed"));

        var response = (await AssistAsync()).Response!;

        response.DegradedReason.Should().Be("product_not_indexed");
        response.DegradedReason.Should().NotBe("ai_unavailable",
            "a piece added after the last index synchronisation is a state that fixes itself, and "
            + "reading it as an outage is what sent people looking for a fault that was not there");
    }

    [Fact]
    public async Task SalesAssist_WhenSwitchedOff_ReportsThatReason()
    {
        _options.EnabledByDefault = false;

        var response = (await AssistAsync()).Response!;

        response.DegradedReason.Should().Be("switched_off");
        VerifyNoAiCall();
    }

    [Fact]
    public async Task SalesAssist_WhenCredentialRejected_ReportsThatReason()
    {
        GatewayThrows(new AiGatewayConfigurationException("401"));

        (await AssistAsync()).Response!.DegradedReason.Should().Be("credential_rejected");
    }

    [Fact]
    public async Task SalesAssist_WhenHealthy_ReportsNoReason()
    {
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M")));

        var response = (await AssistAsync()).Response!;

        response.AiAvailable.Should().BeTrue();
        response.DegradedReason.Should().BeNull("nothing degraded, so there is nothing to explain");
    }

    /// <remarks>
    /// The requirement is that the screen and the log cannot disagree for one trace. This asserts
    /// it across every reason rather than one, because the failure it guards against is a later
    /// change updating one of the two and not the other.
    /// </remarks>
    [Theory]
    [MemberData(nameof(GatewayFailures))]
    public async Task SalesAssist_WhenDegraded_ReasonMatchesTheLogLineForTheSameTrace(AiGatewayException failure)
    {
        GatewayThrows(failure);

        var response = (await AssistAsync()).Response!;
        var stage = StageLine();

        response.DegradedReason.Should().NotBeNull();
        stage.Property("DegradedReason").Should().Be(response.DegradedReason);
        stage.Property("TraceId").Should().Be(response.TraceId);
    }

    [Fact]
    public async Task SalesAssist_WhenSwitchedOff_DoesNotCallAi()
    {
        _options.EnabledByDefault = false;

        var response = (await AssistAsync()).Response!;

        response.AiAvailable.Should().BeFalse();
        VerifyNoAiCall();
        StageLine().Property("DegradedReason").Should().Be("switched_off",
            "the log must say the switch did it, not an outage");
    }

    [Fact]
    public async Task SalesAssist_SwitchedOnForOnePointOfSale_CallsTheAi()
    {
        _options.EnabledByDefault = false;
        _options.EnabledPointOfSaleIds = [PosId];
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M")));

        (await AssistAsync()).Response!.AiAvailable.Should().BeTrue();
    }

    // ---------------------------------------------------------------- logs

    [Fact]
    public async Task SalesAssist_ResolvedPitchIsNeverLogged()
    {
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M")], citations: [Citation("plata#cuidados", "general")]));

        var response = (await AssistAsync(question: "¿se puede mojar?")).Response!;

        response.PitchStatus.Should().Be(PitchStatus.Generated);
        _logs.Entries.Should().NotContain(e => e.Mentions(response.Pitch!), "not the resolved text, at any level");
        _logs.Entries.Should().NotContain(e => e.Mentions("disponibles por"), "not the template either");
        _logs.Entries.Should().NotContain(e => e.Mentions(39.90m.ToString("C2", Spanish)));
    }

    [Fact]
    public async Task SalesAssist_QuestionIsLoggedOnlyAtDebug()
    {
        const string question = "Mi suegra es alérgica al níquel, ¿le vale?";
        GatewayReturns(Ai(Member(Anchor, "ERIZO-M")));

        await AssistAsync(question: question);

        _logs.At(LogLevel.Debug).Should().Contain(e => e.Mentions(question));
        _logs.Entries.Where(e => e.Level > LogLevel.Debug).Should().NotContain(e => e.Mentions(question));
    }

    [Fact]
    public async Task SalesAssist_LogLine_CarriesTheFieldsOfTheDesign()
    {
        Carry(Sibling, "ERIZO-S", quantity: 5);
        GatewayReturns(Ai([Member(Anchor, "ERIZO-M"), Member(Sibling, "ERIZO-S"), Member(NotCarried, "ERIZO-L")],
            warnings: ["family_has_variants"], citations: [Citation("plata#cuidados", "general")]));

        var response = (await AssistAsync(question: "¿es de ley?")).Response!;

        var line = StageLine();
        line.Level.Should().Be(LogLevel.Information);
        line.Property("TraceId").Should().Be("trace-assist-1");
        line.Property("PointOfSaleId").Should().Be(PosId);
        line.Property("ProductId").Should().Be(Anchor);
        line.Property("Mode").Should().Be("M3");
        line.Property("AiAvailable").Should().Be(true);
        line.Property("PitchStatus").Should().Be("generated");
        line.Property("PitchLength").Should().Be(response.Pitch!.Length);
        line.Property("CitationIds").Should().Be("plata#cuidados");
        line.Property("Warnings").Should().Be("family_has_variants");
        line.Property("MembersReturned").Should().Be(3);
        line.Property("MembersCarried").Should().Be(2);
        line.Property("PromptVersion").Should().Be("assist/v4");
        line.Property("Model").Should().Be("openai/gpt-4o-mini");
        line.Property("PromptTokens").Should().Be(900);
        line.Property("CompletionTokens").Should().Be(60);
        line.Property("TotalMs").Should().NotBeNull();
        line.Property("AiMs").Should().NotBeNull();
    }

    // ---------------------------------------------------------------- helpers

    private SalesAssistService CreateService() => new(
        _gateway.Object,
        _repository.Object,
        _families.Object,
        _userPointOfSale.Object,
        _fileStorage.Object,
        _traceContext.Object,
        Mock.Of<IOptionsMonitor<AiSalesAssistOptions>>(m => m.CurrentValue == _options),
        new FakeTimeProvider(),
        // Trace, so the debug-only question is observable: the privacy assertion needs to see it
        // down there in order to prove it stays there.
        LoggerFactory.Create(builder => builder.SetMinimumLevel(LogLevel.Trace).AddProvider(_logs))
            .CreateLogger<SalesAssistService>());

    private Task<SalesAssistResult> AssistAsync(string? question = null, bool isAdmin = false) =>
        CreateService().AssistAsync(
            Anchor,
            new SalesAssistRequest { PointOfSaleId = PosId, Question = question },
            UserId,
            isAdmin ? "Administrator" : "Operator",
            isAdmin);

    private CapturedLogEntry StageLine() => _logs.Entries.Last(e => e.Template.StartsWith("stage=sales_assist ", StringComparison.Ordinal));

    private void Carry(Guid id, string sku, decimal price = 30m, int quantity = 1) =>
        _carried.Add(new AssistedSearchRow
        {
            ProductId = id,
            Sku = sku,
            Name = "Producto " + sku,
            Price = price,
            Quantity = quantity,
            PrimaryPhotoFileName = sku + ".jpg",
            CollectionName = "Mar"
        });

    private void FamilyOf(Guid productId, params (Guid Id, string Label)[] members)
    {
        var family = new ProductFamily { Name = "Pendiente erizo" };
        var order = 0;
        foreach (var (id, label) in members)
        {
            family.Members.Add(new ProductFamilyMember
            {
                ProductFamilyId = family.Id, ProductId = id, VariantLabel = label, SortOrder = order++
            });
        }

        _families.Setup(f => f.GetByProductIdAsync(productId)).ReturnsAsync(family);
    }

    private void GatewayReturns(AiAssistSaleResponse response) =>
        _gateway
            .Setup(g => g.AssistSaleAsync(It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(response);

    private void GatewayThrows(Exception exception) =>
        _gateway
            .Setup(g => g.AssistSaleAsync(It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(exception);

    private void VerifyNoAiCall() =>
        _gateway.Verify(
            g => g.AssistSaleAsync(It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Never);

    private static AiAssistGroupMember Member(Guid id, string sku, string? variant = null) =>
        new() { ProductId = id.ToString(), Sku = sku, VariantLabel = variant, Materials = ["plata"], MatchReasons = ["anchor"] };

    private static AiAssistSaleResponse Ai(params AiAssistGroupMember[] members) => Ai(members, warnings: null);

    private static AiAssistSaleResponse Ai(
        AiAssistGroupMember[] members,
        string pitch = Template,
        string? promptVersion = "assist/v4",
        string[]? warnings = null,
        AiCitation[]? citations = null) => new()
    {
        TraceId = "trace-assist-1",
        EffectivePosId = PosId.ToString(),
        Intent = "product_pitch",
        Groups = [new AiAssistGroup { FamilyId = "fam-1", FamilyLabel = "Pendiente erizo", Members = [.. members] }],
        Pitch = pitch,
        PromptVersion = promptVersion,
        Warnings = [.. warnings ?? []],
        Citations = [.. citations ?? []],
        Usage = new AiUsage { PromptTokens = 900, CompletionTokens = 60, TotalTokens = 960, Model = "openai/gpt-4o-mini" }
    };

    private static AiCitation Citation(string id, string claimScope) => new()
    {
        CitationId = id,
        DocumentTitle = "Doc " + id,
        SectionTitle = "Sección",
        DocType = claimScope == "establecimiento" ? "politica" : "material",
        ClaimScope = claimScope,
        Score = 0.7,
        Snippet = "Fragmento."
    };
}
