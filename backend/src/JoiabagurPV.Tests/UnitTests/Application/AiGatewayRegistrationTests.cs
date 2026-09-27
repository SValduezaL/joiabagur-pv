using FluentAssertions;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.Extensions;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// Start-up validation exists to remove the most banal cause of an unexplainable 401: a
/// configuration key that was never set. Lazy validation would surface it inside a request
/// instead, which is the failure mode being designed out.
/// </summary>
public class AiGatewayRegistrationTests
{
    private const string ValidSecret = "test-jwt-secret-0123456789abcdefghij";

    private static ServiceProvider BuildProvider(Dictionary<string, string?> settings)
    {
        var configuration = new ConfigurationBuilder().AddInMemoryCollection(settings).Build();

        var services = new ServiceCollection();
        services.AddLogging();
        services.AddSingleton<ITraceContextAccessor>(new FixedTraceContextAccessor());
        services.AddAiGateway(configuration);

        return services.BuildServiceProvider();
    }

    /// <summary>Runs the same validation the host runs on start-up.</summary>
    private static Action ValidateStartup(ServiceProvider provider) =>
        () => provider.GetRequiredService<IStartupValidator>().Validate();

    [Fact]
    public void AddAiGateway_WhenSecretMissing_FailsOnStart()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001"
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*JwtSecret*", "the error must name the key that is missing");
    }

    [Fact]
    public void AddAiGateway_WhenSecretTooShortForHs256_FailsOnStart()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = "short"
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*JwtSecret*");
    }

    [Fact]
    public void AddAiGateway_WhenBaseUrlIsNotAbsolute_FailsOnStart()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*BaseUrl*", "the error must name the offending key");
    }

    [Fact]
    public void AddAiGateway_WithValidConfiguration_ResolvesTheClient()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret
        });

        ValidateStartup(provider).Should().NotThrow();
        provider.GetRequiredService<IAiGatewayClient>().Should().NotBeNull();
        provider.GetRequiredService<IAiServiceTokenFactory>().Should().NotBeNull();
    }

    /// <summary>
    /// A disabled integration must not be able to stop the API from starting, even if its
    /// remaining settings are absent.
    /// </summary>
    [Fact]
    public void AddAiGateway_WhenDisabled_RegistersNothingAndDoesNotValidate()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:Enabled"] = "false"
        });

        // Nothing was registered, so there is no start-up validation to run and nothing to resolve.
        provider.GetService<IStartupValidator>().Should().BeNull();
        provider.GetService<IAiGatewayClient>().Should().BeNull();
    }

    /// <summary>
    /// The enrichment family exists as a separate named client so its circuit breaker cannot
    /// take retrieval down with it. That separation is only real if the client is actually
    /// registered under its own name and given its own budget from configuration.
    /// </summary>
    [Fact]
    public void AddAiGateway_RegistersTheEnrichmentClientWithItsOwnConfiguredBudget()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:EnrichTimeoutMs"] = "45000"
        });

        ValidateStartup(provider).Should().NotThrow();

        var factory = provider.GetRequiredService<IHttpClientFactory>();

        factory.CreateClient(AiGatewayClient.EnrichClientName).Should().NotBeNull(
            "enrichment must resolve under its own name, or it would share the retrieval breaker");
        factory.CreateClient(AiGatewayClient.RetrievalClientName).Should().NotBeNull();

        provider.GetRequiredService<IOptions<AiGatewayOptions>>().Value.EnrichTimeoutMs
            .Should().Be(45000,
                "the budget must come from configuration rather than from a framework default, "
                + "whose value contradicts the agreed limits");
    }

    /// <summary>
    /// The outer budget must cover the worst case the AI service declares inside, or this side
    /// throws away answers the service was still entitled to deliver.
    /// </summary>
    [Fact]
    public void AddAiGateway_WhenAssistBudgetBelowServiceWorstCase_FailsAtStartup()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:AssistTimeoutMs"] = "5000"
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*AssistTimeoutMs*", "the error must name the key")
            .WithMessage("*MAX_PITCH_PROVIDER_CALLS*PITCH_TIMEOUT_SECONDS*",
                "and the constants of the AI service that fix the floor");
    }

    [Fact]
    public void AddAiGateway_WithTheAssistBudgetAtTheFloor_Starts()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:AssistTimeoutMs"] = AiGatewayOptions.MinimumAssistTimeoutMs.ToString()
        });

        ValidateStartup(provider).Should().NotThrow();
    }

    /// <summary>
    /// The generative client exists under its own name so its circuit cannot take retrieval down
    /// with it, and its budget comes from configuration — ten seconds unless configured.
    /// </summary>
    [Fact]
    public void AddAiGateway_RegistersTheAssistClientWithItsOwnConfiguredBudget()
    {
        using var defaults = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret
        });

        ValidateStartup(defaults).Should().NotThrow();
        defaults.GetRequiredService<IHttpClientFactory>().CreateClient(AiGatewayClient.AssistClientName)
            .Should().NotBeNull("the generative route must resolve under its own name");
        defaults.GetRequiredService<IOptions<AiGatewayOptions>>().Value.AssistTimeoutMs
            .Should().Be(10_000);

        using var configured = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:AssistTimeoutMs"] = "12000"
        });

        ValidateStartup(configured).Should().NotThrow();
        configured.GetRequiredService<IOptions<AiGatewayOptions>>().Value.AssistTimeoutMs
            .Should().Be(12_000);
    }

    /// <summary>
    /// The agent's floor is the service's own wall-clock ceiling, and the failure mode of going
    /// under it is worse than the assist route's: exceeding the deadline is a <em>degradation</em>
    /// on the Python side, so a shorter outer budget replaces a partial answer the service already
    /// paid for in full with nothing at all.
    /// </summary>
    [Fact]
    public void AddAiGateway_WhenAgentBudgetBelowTheServicesCeiling_FailsAtStartup()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:AgentTimeoutMs"] = "12000"
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*AgentTimeoutMs*", "the error must name the key")
            .WithMessage("*AGENT_DEADLINE_SECONDS*",
                "and the constant of the AI service that fixes the floor");
    }

    [Fact]
    public void AddAiGateway_WithTheAgentBudgetAtTheFloor_Starts()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:AgentTimeoutMs"] = AiGatewayOptions.MinimumAgentTimeoutMs.ToString()
        });

        ValidateStartup(provider).Should().NotThrow();
    }

    /// <summary>
    /// The agent client exists under its own name so a slow conversation cannot open the generative
    /// circuit, and its budget comes from configuration — eighteen seconds unless configured.
    /// </summary>
    [Fact]
    public void AddAiGateway_RegistersTheAgentClientWithItsOwnConfiguredBudget()
    {
        using var defaults = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret
        });

        ValidateStartup(defaults).Should().NotThrow();
        defaults.GetRequiredService<IHttpClientFactory>().CreateClient(AiGatewayClient.AgentClientName)
            .Should().NotBeNull("the agent must resolve under its own name");

        var options = defaults.GetRequiredService<IOptions<AiGatewayOptions>>().Value;
        options.AgentTimeoutMs.Should().Be(18_000);
        options.AgentTimeoutMs.Should().NotBe(options.AssistTimeoutMs,
            "the agent's median latency is of the order of the total the generative route declares "
            + "as its ceiling, so sharing that budget would cut a large share of agent requests");

        using var configured = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:AgentTimeoutMs"] = "20000"
        });

        ValidateStartup(configured).Should().NotThrow();
        configured.GetRequiredService<IOptions<AiGatewayOptions>>().Value.AgentTimeoutMs
            .Should().Be(20_000);
    }

    [Fact]
    public void AddAiGateway_WhenAgentBudgetIsNotPositive_FailsOnStart()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:AgentTimeoutMs"] = "0"
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*time budgets*");
    }

    [Fact]
    public void AddAiGateway_WhenEnrichBudgetIsNotPositive_FailsOnStart()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiGateway:BaseUrl"] = "http://localhost:8001",
            ["AiGateway:JwtSecret"] = ValidSecret,
            ["AiGateway:EnrichTimeoutMs"] = "0"
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*time budgets*");
    }

    private sealed class FixedTraceContextAccessor : ITraceContextAccessor
    {
        public string CurrentTraceId => "trace-registration-test";
    }
}

/// <summary>
/// Start-up validation of the review thresholds.
/// </summary>
/// <remarks>
/// These numbers are meant to be recalibrated against the evaluation golden set, which is why
/// they live in configuration. That is also what makes validating them at start-up necessary: a
/// value outside zero to one is a plausible typo, and lazily it would surface only after a batch
/// had already been routed by a rule that cannot be satisfied.
/// </remarks>
public class ProfileReviewRegistrationTests
{
    private static ServiceProvider BuildProvider(Dictionary<string, string?> settings)
    {
        var configuration = new ConfigurationBuilder().AddInMemoryCollection(settings).Build();

        var services = new ServiceCollection();
        services.AddProfileReview(configuration);

        return services.BuildServiceProvider();
    }

    private static Action ValidateStartup(ServiceProvider provider) =>
        () => provider.GetRequiredService<IStartupValidator>().Validate();

    [Theory]
    [InlineData("1.5")]
    [InlineData("-0.1")]
    public void AddProfileReview_WhenTagThresholdIsOutOfRange_FailsOnStart(string value)
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["ProfileReview:TagAutoApproveThreshold"] = value
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*TagAutoApproveThreshold*", "the error must name the offending key");
    }

    [Fact]
    public void AddProfileReview_WhenMinimumConfidenceIsOutOfRange_FailsOnStart()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["ProfileReview:MinimumFieldConfidence"] = "2"
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage("*MinimumFieldConfidence*");
    }

    [Fact]
    public void AddProfileReview_WithNoConfiguration_UsesTheDocumentedDefaults()
    {
        using var provider = BuildProvider([]);

        ValidateStartup(provider).Should().NotThrow(
            "the thresholds have documented starting points, so an installation that has not "
            + "calibrated them yet must still boot");

        var options = provider.GetRequiredService<IOptions<ProfileReviewOptions>>().Value;
        options.TagAutoApproveThreshold.Should().Be(0.80);
        options.MinimumFieldConfidence.Should().Be(0.50);
    }

    [Fact]
    public void AddProfileReview_ReadsTheThresholdFromConfiguration()
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["ProfileReview:TagAutoApproveThreshold"] = "0.65"
        });

        provider.GetRequiredService<IOptions<ProfileReviewOptions>>().Value
            .TagAutoApproveThreshold.Should().Be(0.65);
    }
}
