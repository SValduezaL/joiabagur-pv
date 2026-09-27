using FluentAssertions;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.Extensions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Xunit;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// The configuration of the free-query endpoint: its documented defaults, its own allowance, and
/// the start-up validation that refuses a combination which would otherwise fail silently.
/// </summary>
public class FreeQuerySearchConfigurationTests
{
    // ---------------------------------------------------------------- defaults

    [Fact]
    public void Options_AreSwitchedOffByDefault()
    {
        var options = new AiFreeQuerySearchOptions();

        options.EnabledByDefault.Should().BeFalse("enabling a shop is an explicit act");
        options.EnabledPointOfSaleIds.Should().BeEmpty();
        options.IsEnabledFor(Guid.NewGuid()).Should().BeFalse();
    }

    /// <remarks>
    /// Ten and not search's thirty: the cost profile is the card's — a routing call, a corpus
    /// consultation and a generation — and this figure is what the screen states before the
    /// operator presses, so it is part of the interface rather than only of the infrastructure.
    /// </remarks>
    [Fact]
    public void Options_RateLimit_DefaultsToTenPerMinute()
    {
        var options = new AiFreeQuerySearchOptions();

        options.RateLimitPermitLimit.Should().Be(10);
        options.RateLimitWindowSeconds.Should().Be(60);
    }

    [Fact]
    public void Options_HaveTheirOwnSection_NotTheCards()
    {
        AiFreeQuerySearchOptions.SectionName.Should().Be("AiFreeQuerySearch");
        AiFreeQuerySearchOptions.SectionName.Should().NotBe(AiSalesAssistOptions.SectionName,
            "the card is opened once per piece and this panel is used in bursts, so a shared "
            + "quota would leave whichever one the operator reached second unable to work");
    }

    [Fact]
    public void Options_EnableOneShopWithoutEnablingTheRest()
    {
        var mine = Guid.NewGuid();
        var options = new AiFreeQuerySearchOptions { EnabledPointOfSaleIds = [mine] };

        options.IsEnabledFor(mine).Should().BeTrue();
        options.IsEnabledFor(Guid.NewGuid()).Should().BeFalse();
    }

    // ---------------------------------------------------------------- start-up validation

    [Theory]
    [InlineData("RateLimitPermitLimit", "0")]
    [InlineData("RateLimitWindowSeconds", "0")]
    [InlineData("CandidateWindow", "0")]
    [InlineData("CandidateWindow", "21")]
    [InlineData("MaxPageSize", "0")]
    [InlineData("MaxPageSize", "51")]
    [InlineData("DefaultPageSize", "0")]
    public void FreeQueryOptions_WhenInvalid_FailsAtStartup(string key, string value)
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            [$"AiFreeQuerySearch:{key}"] = value
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>()
            .WithMessage($"*AiFreeQuerySearch:{key}*", "the error must name the offending key");
    }

    /// <remarks>
    /// The two relationships no per-key range can express, and both fail <em>silently</em> at
    /// request time: a default page larger than the maximum, and a candidate window too small to
    /// fill a page. Neither raises anything — the endpoint simply serves the wrong number of
    /// results, for as long as nobody counts them — which is why they are refused at boot instead
    /// of clamped.
    /// </remarks>
    [Theory]
    [InlineData("10", "5", "5")]
    [InlineData("5", "20", "3")]
    public void FreeQueryOptions_WhenInternallyInconsistent_FailsAtStartup(
        string defaultPage, string maxPage, string window)
    {
        using var provider = BuildProvider(new Dictionary<string, string?>
        {
            ["AiFreeQuerySearch:DefaultPageSize"] = defaultPage,
            ["AiFreeQuerySearch:MaxPageSize"] = maxPage,
            ["AiFreeQuerySearch:CandidateWindow"] = window
        });

        ValidateStartup(provider).Should().Throw<OptionsValidationException>();
    }

    [Fact]
    public void FreeQueryOptions_WithTheDefaults_StartUpCleanly()
    {
        using var provider = BuildProvider([]);

        ValidateStartup(provider).Should().NotThrow(
            "the documented defaults must be a configuration the application can boot with");
    }

    [Fact]
    public void Inconsistencies_NamesBothValues_SoTheMessageIsActionable()
    {
        // The window is left wide enough that only the page-size relationship is violated, so
        // the assertion is about the message and not about how many fired.
        var options = new AiFreeQuerySearchOptions
        {
            DefaultPageSize = 10,
            MaxPageSize = 5,
            CandidateWindow = 10
        };

        options.Inconsistencies().Should().ContainSingle()
            .Which.Should().Contain("10").And.Contain("5");
    }

    // ---------------------------------------------------------------- arrangement

    private static ServiceProvider BuildProvider(Dictionary<string, string?> settings)
    {
        var configuration = new ConfigurationBuilder().AddInMemoryCollection(settings).Build();

        var services = new ServiceCollection();
        services.AddFreeQuerySearch(configuration);

        return services.BuildServiceProvider();
    }

    private static Action ValidateStartup(ServiceProvider provider) =>
        () => provider.GetRequiredService<IStartupValidator>().Validate();
}
