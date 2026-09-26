using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace JoiabagurPV.Application.Extensions;

/// <summary>
/// Registers the sale agent endpoint (C42): options with start-up validation and the service that
/// orchestrates one turn of a conversation.
/// </summary>
/// <remarks>
/// A registration of its own, like the free query and the sale card, and for the same reason: the
/// options need the configuration, and <c>AddApplication()</c>'s signature is one the integration
/// tests depend on.
/// </remarks>
public static class AiAgentAssistServiceCollectionExtensions
{
    /// <summary>
    /// Adds the sale agent and validates its configuration at start-up.
    /// </summary>
    /// <remarks>
    /// Validated at boot rather than clamped at request time, which is the rule this project already
    /// applies to its sibling: a misconfigured window produces no error and simply serves the wrong
    /// number of results, for as long as nobody counts them.
    /// </remarks>
    public static IServiceCollection AddAgentAssist(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(configuration);

        const string section = AiAgentAssistOptions.SectionName;

        services
            .AddOptions<AiAgentAssistOptions>()
            .Bind(configuration.GetSection(section))
            .Validate(
                options => options.RateLimitPermitLimit > 0 && options.RateLimitWindowSeconds > 0,
                $"{section}:RateLimitPermitLimit and {section}:RateLimitWindowSeconds must be positive.")
            .Validate(
                options => options.CandidateWindow >= 1 && options.CandidateWindow <= 20,
                $"{section}:CandidateWindow must be between 1 and 20, which is the largest top_k the frozen jbg-ai contract accepts for the assist route.")
            .ValidateOnStart();

        services.AddScoped<IAgentAssistService, AgentAssistService>();

        return services;
    }
}
