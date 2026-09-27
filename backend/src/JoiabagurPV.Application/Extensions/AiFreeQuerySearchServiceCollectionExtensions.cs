using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace JoiabagurPV.Application.Extensions;

/// <summary>
/// Registers the free-query search endpoint (C40): options with start-up validation and the
/// service that orchestrates it.
/// </summary>
/// <remarks>
/// A registration of its own, like assisted search and the sale card, and for the same reason:
/// the options need the configuration, and <c>AddApplication()</c>'s signature is one the
/// integration tests depend on.
/// </remarks>
public static class AiFreeQuerySearchServiceCollectionExtensions
{
    /// <summary>
    /// Adds the free-query search and validates its configuration at start-up.
    /// </summary>
    /// <remarks>
    /// **Validated at boot rather than clamped at request time.** A page size larger than the
    /// maximum, or a candidate window too small to fill a page, produces no error at all: the
    /// endpoint simply serves the wrong number of results, for as long as nobody counts them.
    /// Refusing to start names the key and the value; clamping would make the mistake permanent
    /// and invisible, which is the failure mode this whole change exists to remove.
    /// </remarks>
    public static IServiceCollection AddFreeQuerySearch(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(configuration);

        const string section = AiFreeQuerySearchOptions.SectionName;

        services
            .AddOptions<AiFreeQuerySearchOptions>()
            .Bind(configuration.GetSection(section))
            .Validate(
                options => options.RateLimitPermitLimit > 0 && options.RateLimitWindowSeconds > 0,
                $"{section}:RateLimitPermitLimit and {section}:RateLimitWindowSeconds must be positive.")
            .Validate(
                options => options.CandidateWindow >= 1 && options.CandidateWindow <= 20,
                $"{section}:CandidateWindow must be between 1 and 20, which is the largest top_k the frozen jbg-ai contract accepts for the assist route.")
            .Validate(
                options => options.MaxPageSize >= 1 && options.MaxPageSize <= 50,
                $"{section}:MaxPageSize must be between 1 and 50, the pagination ceiling of the project.")
            .Validate(
                options => options.DefaultPageSize >= 1,
                $"{section}:DefaultPageSize must be at least 1.")
            .Validate(
                options => !options.Inconsistencies().Any(),
                $"{section} is internally inconsistent; see AiFreeQuerySearchOptions.Inconsistencies().")
            .ValidateOnStart();

        services.AddScoped<IFreeQuerySearchService, FreeQuerySearchService>();

        return services;
    }
}
