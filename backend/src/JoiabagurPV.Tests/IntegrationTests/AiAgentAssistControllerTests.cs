using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.DTOs.Auth;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Domain.Entities;
using JoiabagurPV.Tests.TestHelpers;
using JoiabagurPV.Tests.TestHelpers.Mothers;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace JoiabagurPV.Tests.IntegrationTests;

/// <summary>
/// The sale-agent endpoint over HTTP: its route, its authorisation, its transcript caps and the
/// availability probe that has to report it apart from the assisted answer. C42.
/// </summary>
/// <remarks>
/// Its own host, like the other rate policies, because the shared factory raises every allowance
/// out of the way and a policy nobody can reach is a policy nobody can test.
/// </remarks>
[Collection(IntegrationTestCollection.Name)]
public class AiAgentAssistControllerTests : IAsyncLifetime
{
    private readonly ApiWebApplicationFactory _sharedFactory;
    private readonly HttpClient _warmUpClient;
    private readonly CountingAgentGateway _gateway = new();

    private WebApplicationFactory<Program> _factory = null!;
    private PointOfSale _pos = null!;
    private PointOfSale _otherPos = null!;
    private Product _product = null!;
    private Product _substitute = null!;
    private HttpClient _operator = null!;
    private HttpClient _administrator = null!;

    public AiAgentAssistControllerTests(ApiWebApplicationFactory sharedFactory)
    {
        _sharedFactory = sharedFactory;
        _warmUpClient = sharedFactory.CreateClient();
    }

    public async Task InitializeAsync()
    {
        await _sharedFactory.ResetDatabaseAsync();

        using var mother = new TestDataMother(_sharedFactory.Services);

        // Phone pinned: the generator produces numbers of varying length and the column is
        // varchar(20), so leaving it to chance fails intermittently.
        _pos = await mother.PointOfSale()
            .WithCode("AG-POS").WithName("Agent Shop")
            .WithAddress("Test Address").WithPhone("600123456").CreateAsync();

        _otherPos = await mother.PointOfSale()
            .WithCode("AG-OTHER").WithName("Another Shop")
            .WithAddress("Test Address").WithPhone("600123456").CreateAsync();

        _product = await mother.Product()
            .WithSku("SKU-AG-1").WithName("Anillo de plata").WithPrice(39.9m).CreateAsync();

        _substitute = await mother.Product()
            .WithSku("SKU-AG-2").WithName("Anillo de acero").WithPrice(19.9m).CreateAsync();

        await mother.Inventory()
            .WithProduct(_product.Id).WithPointOfSale(_pos.Id).WithQuantity(4).CreateAsync();
        await mother.Inventory()
            .WithProduct(_substitute.Id).WithPointOfSale(_pos.Id).WithQuantity(7).CreateAsync();

        await mother.User().WithUsername("agone").AsOperator().AssignedTo(_pos.Id).CreateAsync();
        await mother.User().WithUsername("agadmin").AsAdmin().CreateAsync();

        _gateway.MatchProductId = _product.Id.ToString();
        _gateway.SubstituteProductId = _substitute.Id.ToString();

        _factory = _sharedFactory.WithWebHostBuilder(builder =>
        {
            builder.UseSetting("AiAgentAssist:EnabledByDefault", "true");
            builder.UseSetting("AiFreeQuerySearch:EnabledByDefault", "true");
            builder.ConfigureServices(services => services.AddScoped<IAiGatewayClient>(_ => _gateway));
        });

        _operator = await AuthenticateAsync("agone");
        _administrator = await AuthenticateAsync("agadmin");
    }

    public Task DisposeAsync()
    {
        _factory?.Dispose();
        return Task.CompletedTask;
    }

    // ---------------------------------------------------------------- the route

    [Fact]
    public async Task Agent_AnswersWithGroupsHydratedFromTheCatalogAndLabelledByProvenance()
    {
        var response = await AskAsync(_operator);

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = (await response.Content.ReadFromJsonAsync<AgentAssistResponse>())!;

        body.AiAvailable.Should().BeTrue();
        body.Groups.Should().HaveCount(2);
        body.Groups.Select(group => group.Origin).Should().Equal("catalogo", "sustitutos");

        // Price comes from the catalog, never from the model — and the substitute is hydrated on
        // exactly the same terms as the match.
        body.Groups[0].Members.Should().ContainSingle().Which.Price.Should().Be(39.9m);
        body.Groups[1].Members.Should().ContainSingle().Which.Price.Should().Be(19.9m);

        // And the five fields the agent adds reach the caller.
        body.StopReason.Should().Be("sin_mas_herramientas");
        body.Iterations.Should().Be(2);
        body.ToolCallsUsed.Should().Be(3);
        body.Trace.Should().NotBeEmpty();
        body.AgentPromptVersion.Should().Be("assist/v6");
    }

    [Fact]
    public async Task Agent_WhenUnauthenticated_Returns401()
    {
        // A fresh client from the factory: the shared one carries the cookies of every login it
        // performed, so it is not anonymous.
        var anonymous = _factory.CreateClient();

        var response = await anonymous.PostAsJsonAsync("/api/ai/search/agent", Conversation());

        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task Agent_ForAnUnassignedPointOfSale_IsForbidden()
    {
        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/agent",
            new AgentAssistRequest { Turns = Turns(), PointOfSaleId = _otherPos.Id });

        response.StatusCode.Should().Be(HttpStatusCode.Forbidden);
    }

    /// <summary>
    /// The same rule the free-query route applies, copied and not tightened: the wider scope is
    /// open to both roles. Two sibling panels with two different authorisation rules break without
    /// any test failing.
    /// </summary>
    [Fact]
    public async Task Agent_ForTheEveryShopScope_IsServedToBothRoles()
    {
        foreach (var client in new[] { _operator, _administrator })
        {
            var response = await client.PostAsJsonAsync(
                "/api/ai/search/agent",
                new AgentAssistRequest { Turns = Turns(), PointOfSaleId = null });

            response.StatusCode.Should().Be(HttpStatusCode.OK);

            var body = (await response.Content.ReadFromJsonAsync<AgentAssistResponse>())!;
            body.PointOfSaleId.Should().BeNull(
                "the response echoes the absence rather than substituting a shop for it");
        }
    }

    [Fact]
    public async Task Agent_WithABlankPointOfSale_Returns400()
    {
        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/agent",
            new AgentAssistRequest { Turns = Turns(), PointOfSaleId = Guid.Empty });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    // ---------------------------------------------------------------- the three caps

    /// <summary>
    /// <strong>The cap the other two do not imply, and the trap it exists to avoid.</strong> Twelve
    /// turns each inside the per-turn limit still exceed the total, because the argument travels
    /// back in the assistant's turns. The assertion is not only the 400: it is that no provider call
    /// was spent learning it.
    /// </summary>
    [Fact]
    public async Task AgentAssist_WhenTranscriptExceedsItsCaps_IsRefusedBeforeTheCall()
    {
        var before = _gateway.AgentCalls;

        var overTheTotal = Enumerable.Range(0, 10)
            .Select(index => new AgentAssistTurnDto
            {
                Role = index % 2 == 0 ? "operario" : "asistente",
                Text = new string('a', 450)
            })
            .ToList();

        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/agent",
            new AgentAssistRequest { Turns = overTheTotal, PointOfSaleId = _pos.Id });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        (await response.Content.ReadAsStringAsync()).Should().Contain("4000",
            "the message names the cap that was exceeded, in Spanish");

        _gateway.AgentCalls.Should().Be(before,
            "a caller must not spend a provider call to be told its request was malformed");
    }

    [Fact]
    public async Task Agent_WhenATurnIsTooLong_IsRefusedBeforeTheCall()
    {
        var before = _gateway.AgentCalls;

        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/agent",
            new AgentAssistRequest
            {
                Turns = [new AgentAssistTurnDto { Role = "operario", Text = new string('a', 501) }],
                PointOfSaleId = _pos.Id
            });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        _gateway.AgentCalls.Should().Be(before);
    }

    [Fact]
    public async Task Agent_WhenThereAreTooManyTurns_IsRefusedBeforeTheCall()
    {
        var before = _gateway.AgentCalls;

        var thirteen = Enumerable.Range(0, 13)
            .Select(index => new AgentAssistTurnDto
            {
                Role = index % 2 == 0 ? "operario" : "asistente",
                Text = "corto"
            })
            .ToList();

        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/agent",
            new AgentAssistRequest { Turns = thirteen, PointOfSaleId = _pos.Id });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        _gateway.AgentCalls.Should().Be(before);
    }

    [Fact]
    public async Task Agent_WithNoOperatorTurn_IsRefusedBeforeTheCall()
    {
        var before = _gateway.AgentCalls;

        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/agent",
            new AgentAssistRequest
            {
                Turns = [new AgentAssistTurnDto { Role = "asistente", Text = "te enseño estos" }],
                PointOfSaleId = _pos.Id
            });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        _gateway.AgentCalls.Should().Be(before,
            "the turn being answered is the last of the operator's; a transcript of nothing but "
            + "assistant turns asks no question");
    }

    [Fact]
    public async Task Agent_WithAnEmptyTranscript_IsRefusedBeforeTheCall()
    {
        var before = _gateway.AgentCalls;

        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/agent",
            new AgentAssistRequest { Turns = [], PointOfSaleId = _pos.Id });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        _gateway.AgentCalls.Should().Be(before);
    }

    // ---------------------------------------------------------------- the probe

    /// <summary>
    /// <strong>The agent's switch reported apart from the assisted answer's.</strong> Deriving one
    /// from the other would tell the screen the agent is available while every agent request came
    /// back degraded.
    /// </summary>
    [Fact]
    public async Task AgentAvailability_WithoutPointOfSale_ReportsTheAgentSwitch()
    {
        var response = await _operator.GetAsync("/api/ai/search/availability");

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = (await response.Content.ReadFromJsonAsync<AiSearchAvailabilityResponse>())!;

        body.AgentAvailable.Should().BeTrue();
        body.AgentUnavailableReason.Should().BeNull();
        body.PointOfSaleId.Should().BeNull("an absent point of sale is the wider scope");
    }

    [Fact]
    public async Task AgentAvailability_WhenTheAssistedAnswerIsOnAndTheAgentOff_ReportsThemApart()
    {
        // The state the probe exists for: the agent has a credential chain of its own, so a
        // deployment can have the assisted answer configured and the agent not.
        using var mixed = _sharedFactory.WithWebHostBuilder(builder =>
        {
            builder.UseSetting("AiFreeQuerySearch:EnabledByDefault", "true");
            builder.UseSetting("AiSalesAssist:EnabledByDefault", "true");
            builder.UseSetting("AiAgentAssist:EnabledByDefault", "false");
            builder.ConfigureServices(services => services.AddScoped<IAiGatewayClient>(_ => _gateway));
        });

        var client = await AuthenticateAsync("agone", mixed);

        var body = (await (await client.GetAsync($"/api/ai/search/availability?pointOfSaleId={_pos.Id}"))
            .Content.ReadFromJsonAsync<AiSearchAvailabilityResponse>())!;

        body.AssistedAnswerAvailable.Should().BeTrue();
        body.AgentAvailable.Should().BeFalse();
        body.AgentUnavailableReason.Should().Be("switched_off");
        body.AssistedAnswerUnavailableReason.Should().BeNull(
            "the reason shown on the agent's card must be the agent's own");
    }

    [Fact]
    public async Task Agent_WhenSwitchedOff_IsServedWithTheReasonAndSpendsNoCall()
    {
        using var off = _sharedFactory.WithWebHostBuilder(builder =>
        {
            builder.UseSetting("AiAgentAssist:EnabledByDefault", "false");
            builder.ConfigureServices(services => services.AddScoped<IAiGatewayClient>(_ => _gateway));
        });

        var client = await AuthenticateAsync("agone", off);
        var before = _gateway.AgentCalls;

        var response = await client.PostAsJsonAsync("/api/ai/search/agent", Conversation());

        response.StatusCode.Should().Be(HttpStatusCode.OK, "a switch is not an error");

        var body = (await response.Content.ReadFromJsonAsync<AgentAssistResponse>())!;
        body.AiAvailable.Should().BeFalse();
        body.DegradedReason.Should().Be("switched_off");
        _gateway.AgentCalls.Should().Be(before);
    }

    // ---------------------------------------------------------------- arrangement

    private static List<AgentAssistTurnDto> Turns() =>
        [new AgentAssistTurnDto { Role = "operario", Text = "busco un anillo de plata" }];

    private AgentAssistRequest Conversation() => new()
    {
        Turns = Turns(),
        PointOfSaleId = _pos.Id
    };

    private Task<HttpResponseMessage> AskAsync(HttpClient client) =>
        client.PostAsJsonAsync("/api/ai/search/agent", Conversation());

    private async Task<HttpClient> AuthenticateAsync(
        string username, WebApplicationFactory<Program>? factory = null)
    {
        var client = (factory ?? _factory).CreateClient();
        var response = await client.PostAsJsonAsync(
            "/api/auth/login", new LoginRequest { Username = username, Password = "Test123!" });
        response.EnsureSuccessStatusCode();
        return client;
    }

    /// <summary>
    /// The agent route of the gateway, answering with a pivot: one catalogue group and one
    /// substitutes group, which is what the provenance field exists for.
    /// </summary>
    private sealed class CountingAgentGateway : ThrowingAiGatewayClient
    {
        private int _agentCalls;

        public int AgentCalls => _agentCalls;

        public string MatchProductId { get; set; } = string.Empty;

        public string SubstituteProductId { get; set; } = string.Empty;

        public override Task<AiAssistAgentResponse> AssistAgentAsync(
            AiAssistAgentRequest request, AiCallScope scope, CancellationToken cancellationToken = default)
        {
            Interlocked.Increment(ref _agentCalls);

            return Task.FromResult(new AiAssistAgentResponse
            {
                Intent = "in_domain",
                Groups =
                [
                    new AiAssistAgentGroup
                    {
                        FamilyId = "fam-ag",
                        FamilyLabel = "Aro fino",
                        Origin = "catalogo",
                        Members =
                        [
                            new AiAssistGroupMember
                            {
                                ProductId = MatchProductId,
                                Sku = "SKU-AG-1",
                                Score = 0.82,
                                Materials = ["plata"],
                                MatchReasons = ["vector"]
                            }
                        ]
                    },
                    new AiAssistAgentGroup
                    {
                        FamilyId = null,
                        FamilyLabel = null,
                        Origin = "sustitutos",
                        Members =
                        [
                            new AiAssistGroupMember
                            {
                                ProductId = SubstituteProductId,
                                Sku = "SKU-AG-2",
                                Score = 0.61,
                                Materials = ["acero"],
                                MatchReasons = []
                            }
                        ]
                    }
                ],
                // No placeholder: assist/v6 forbids them for the agent's task and a hard cause in
                // the service's integrity gate makes that a guarantee.
                Pitch = "De las dos, la de plata es la más sobria y la de acero la más resistente.",
                PromptVersion = "assist/v6",
                Partial = false,
                StopReason = "sin_mas_herramientas",
                Iterations = 2,
                ToolCallsUsed = 3,
                Trace =
                [
                    new AiAgentTraceIteration
                    {
                        Iteration = 1,
                        Tools = [new AiAgentTraceTool { Tool = "buscar_catalogo", Ok = true }],
                        PromptTokens = 3200,
                        CompletionTokens = 60,
                        TotalTokens = 3260,
                        ElapsedMs = 1420.5
                    },
                    new AiAgentTraceIteration
                    {
                        Iteration = 2,
                        Tools =
                        [
                            new AiAgentTraceTool { Tool = "consultar_disponibilidad", Ok = true },
                            new AiAgentTraceTool { Tool = "buscar_sustitutos", Ok = true }
                        ],
                        PromptTokens = 4100,
                        CompletionTokens = 80,
                        TotalTokens = 4180,
                        ElapsedMs = 1980.0
                    }
                ],
                AgentPromptVersion = "assist/v6",
                Usage = new AiAgentUsage
                {
                    PromptTokens = 12876,
                    CompletionTokens = 240,
                    TotalTokens = 13116,
                    Model = "openai/gpt-4o",
                    Calls = 4
                }
            });
        }
    }
}
