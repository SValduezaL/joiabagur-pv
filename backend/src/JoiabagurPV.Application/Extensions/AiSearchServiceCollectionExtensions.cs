using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace JoiabagurPV.Application.Extensions;

/// <summary>
/// Registers assisted search: options with start-up validation, the candidate cache and the
/// orchestrating service.
/// </summary>
public static class AiSearchServiceCollectionExtensions
{
    /// <summary>
    /// Adds assisted search and validates its configuration during host start-up.
    /// </summary>
    /// <remarks>
    /// Options are bound through <c>IOptionsMonitor</c> so the list of enabled points of sale
    /// reloads without a redeploy. That reloadability is the whole reason the switch lives in
    /// configuration instead of in a column, so it is not an incidental detail.
    /// </remarks>
    public static IServiceCollection AddAssistedSearch(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(configuration);

        services
            .AddOptions<AiSearchOptions>()
            .Bind(configuration.GetSection(AiSearchOptions.SectionName))
            .Validate(
                options => options.CandidateWindow >= 1
                           && options.CandidateWindow <= AiSearchRequest.MaxTopK,
                $"{AiSearchOptions.SectionName}:CandidateWindow must be between 1 and {AiSearchRequest.MaxTopK}, which is the largest page size the frozen jbg-ai contract accepts.")
            .Validate(
                options => options.MaxPageSize >= 1 && options.MaxPageSize <= 50,
                $"{AiSearchOptions.SectionName}:MaxPageSize must be between 1 and 50, the pagination ceiling of the project.")
            .Validate(
                options => options.DefaultPageSize >= 1
                           && options.DefaultPageSize <= options.MaxPageSize,
                $"{AiSearchOptions.SectionName}:DefaultPageSize must be at least 1 and no larger than MaxPageSize.")
            .Validate(
                options => options.CandidateCacheTtlSeconds > 0 && options.CandidateCacheSize > 0,
                $"{AiSearchOptions.SectionName} candidate cache lifetime and size must be positive.")
            .Validate(
                options => options.RateLimitPermitLimit > 0 && options.RateLimitWindowSeconds > 0,
                $"{AiSearchOptions.SectionName} rate limit permit count and window must be positive.")
            // Without ValidateOnStart the check is lazy and would surface inside a request, which
            // is exactly the failure mode being removed.
            .ValidateOnStart();

        services.AddSingleton<IAssistedSearchCandidateCache, AssistedSearchCandidateCache>();
        // Shared with the free-query search of C40, which projects the same row shape.
        services.AddScoped<IAssistedSearchResultProjector, AssistedSearchResultProjector>();
        services.AddScoped<IAssistedSearchService, AssistedSearchService>();

        return services;
    }
}
