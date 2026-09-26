using JoiabagurPV.API.Services;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.Interfaces;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.IdentityModel.Tokens;
using System.Security.Claims;
using System.Text;
using System.Text.Json;
using System.Threading.RateLimiting;

namespace JoiabagurPV.API.Extensions;

/// <summary>
/// Names of the rate-limiting policies, so registration and the controllers that opt into them
/// cannot drift apart over a string literal.
/// </summary>
public static class RateLimitPolicies
{
    /// <summary>Login attempts, partitioned by network origin.</summary>
    public const string Login = "LoginRateLimit";

    /// <summary>Assisted search, partitioned by user.</summary>
    public const string AiSearch = "AiSearchRateLimit";

    /// <summary>
    /// Sale assistance (C34), partitioned by user. Its own policy because its route calls the
    /// language model; the substitutes route calls none and uses <see cref="AiSearch"/>.
    /// </summary>
    public const string AiSalesAssist = "AiSalesAssistRateLimit";

    /// <summary>
    /// Free-query search (C40), partitioned by user. Its own policy because its route calls
    /// the language model and the panel is used in bursts; sharing the card's allowance would
    /// leave whichever one the operator reached second unable to work, with no way to know why.
    /// </summary>
    public const string AiFreeQuerySearch = "AiFreeQuerySearchRateLimit";

    /// <summary>
    /// The sale agent (C42), partitioned by user. Its own policy, and here the allowance is set by
    /// the quota rather than by taste: at about 13 000 prompt tokens per request against 25 000
    /// tokens per minute, the system admits roughly one request per minute. Sharing the free query's
    /// allowance would let a handful of conversations exhaust what the cheaper route needs.
    /// </summary>
    public const string AiAgentAssist = "AiAgentAssistRateLimit";
}

/// <summary>
/// Extension methods for configuring API services.
/// </summary>
public static class ServiceCollectionExtensions
{

    /// <summary>
    /// Adds API services to the dependency injection container.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="configuration">The application configuration.</param>
    /// <returns>The service collection with API services added.</returns>
    public static IServiceCollection AddApiServices(this IServiceCollection services, IConfiguration configuration)
    {
        // Configure JSON options for camelCase
        services.AddControllers(options =>
        {
            // Add global filters if needed
        })
        .AddJsonOptions(options =>
        {
            options.JsonSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
            options.JsonSerializerOptions.WriteIndented = false;
        });

        // Configure API behavior
        services.Configure<ApiBehaviorOptions>(options =>
        {
            options.SuppressModelStateInvalidFilter = true; // We'll handle validation manually
        });

        // Add HttpContextAccessor for CurrentUserService
        services.AddHttpContextAccessor();
        services.AddScoped<ICurrentUserService, CurrentUserService>();

        // Correlation identifier for outbound calls (AI gateway). Same layering as
        // CurrentUserService: interface in Application, implementation here.
        services.AddScoped<ITraceContextAccessor, TraceContextAccessor>();

        // Add JWT Authentication
        var jwtSecretKey = configuration["Jwt:SecretKey"] ?? throw new InvalidOperationException("JWT SecretKey not configured");
        var jwtIssuer = configuration["Jwt:Issuer"] ?? "JoiabagurPV";
        var jwtAudience = configuration["Jwt:Audience"] ?? "JoiabagurPV";

        services.AddAuthentication(options =>
        {
            options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
            options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
        })
        .AddJwtBearer(options =>
        {
            options.TokenValidationParameters = new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSecretKey)),
                ValidateIssuer = true,
                ValidIssuer = jwtIssuer,
                ValidateAudience = true,
                ValidAudience = jwtAudience,
                ValidateLifetime = true,
                ClockSkew = TimeSpan.Zero
            };

            // Read token from cookie
            options.Events = new JwtBearerEvents
            {
                OnMessageReceived = context =>
                {
                    // Try to get token from cookie first
                    if (context.Request.Cookies.TryGetValue("access_token", out var token))
                    {
                        context.Token = token;
                    }
                    return Task.CompletedTask;
                }
            };
        });

        services.AddAuthorization();

        // Add rate limiting for login endpoint (disabled in testing)
        var isTestingEnvironment = configuration.GetValue<bool>("Testing:SkipSwagger");
        services.AddRateLimiter(options =>
        {
            options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;

            options.AddPolicy("LoginRateLimit", httpContext =>
                RateLimitPartition.GetFixedWindowLimiter(
                    partitionKey: httpContext.Connection.RemoteIpAddress?.ToString() ?? "unknown",
                    factory: _ => new FixedWindowRateLimiterOptions
                    {
                        // Use high limit for tests, normal limit for production
                        PermitLimit = isTestingEnvironment ? 1000 : 30,
                        Window = TimeSpan.FromMinutes(10),
                        QueueLimit = 0
                    }));

            // Assisted search (C15). Partitioned by user, not by network origin: behind the
            // reverse proxy an entire shop shares one address, so an IP partition would let one
            // operator exhaust the allowance of their colleagues. The login policy partitions by
            // address because it runs before there is a user to partition by.
            //
            // This is a cost control before it is a security control: every assisted search
            // charges a query embedding, and a key held down or a mis-tuned debounce turns into
            // a bill.
            var searchOptions = configuration
                .GetSection(AiSearchOptions.SectionName)
                .Get<AiSearchOptions>() ?? new AiSearchOptions();

            // In testing the limit is raised out of the way so the policy does not interfere
            // with the rest of the suite — unless a test configures one explicitly, which is how
            // the policy itself becomes testable. Without that escape hatch the only way to
            // exercise it would be to issue ten thousand requests.
            var configuredPermitLimit = configuration
                .GetValue<int?>($"{AiSearchOptions.SectionName}:{nameof(AiSearchOptions.RateLimitPermitLimit)}");

            var permitLimit = configuredPermitLimit
                              ?? (isTestingEnvironment ? 10_000 : searchOptions.RateLimitPermitLimit);

            options.AddPolicy(RateLimitPolicies.AiSearch, httpContext =>
                RateLimitPartition.GetFixedWindowLimiter(
                    // Requires HttpContext.User, which the authentication middleware populates.
                    // Program.cs runs UseRateLimiter after UseAuthentication for that reason; if
                    // it ran before, this would silently read an empty principal and partition
                    // every operator of a shop into the one address they share behind the proxy.
                    partitionKey: httpContext.User.FindFirst(ClaimTypes.NameIdentifier)?.Value
                                  ?? httpContext.Connection.RemoteIpAddress?.ToString()
                                  ?? "unknown",
                    factory: _ => new FixedWindowRateLimiterOptions
                    {
                        PermitLimit = permitLimit,
                        Window = TimeSpan.FromSeconds(searchOptions.RateLimitWindowSeconds),
                        QueueLimit = 0
                    }));

            // Sale assistance (C34). Same shape as the search policy — partitioned by user, raised
            // out of the way in testing unless a test sets the limit — with its own allowance,
            // because every request can cost two paid provider calls and the organisation's
            // tokens-per-minute quota is what several operators at once run into first. A 429 is
            // how the caller tells "throttled" from "AI unavailable", which is a 200.
            var salesAssistOptions = configuration
                .GetSection(AiSalesAssistOptions.SectionName)
                .Get<AiSalesAssistOptions>() ?? new AiSalesAssistOptions();

            var salesAssistPermitLimit = configuration
                .GetValue<int?>($"{AiSalesAssistOptions.SectionName}:{nameof(AiSalesAssistOptions.RateLimitPermitLimit)}")
                ?? (isTestingEnvironment ? 10_000 : salesAssistOptions.RateLimitPermitLimit);

            options.AddPolicy(RateLimitPolicies.AiSalesAssist, httpContext =>
                RateLimitPartition.GetFixedWindowLimiter(
                    partitionKey: httpContext.User.FindFirst(ClaimTypes.NameIdentifier)?.Value
                                  ?? httpContext.Connection.RemoteIpAddress?.ToString()
                                  ?? "unknown",
                    factory: _ => new FixedWindowRateLimiterOptions
                    {
                        PermitLimit = salesAssistPermitLimit,
                        Window = TimeSpan.FromSeconds(salesAssistOptions.RateLimitWindowSeconds),
                        QueueLimit = 0
                    }));

            // Free-query search (C40). Same shape again, and its own allowance for the reason
            // its configuration section exists: the card is opened once per piece and the panel
            // is used in bursts, so a shared quota strangles whichever one is reached second.
            var freeQueryOptions = configuration
                .GetSection(AiFreeQuerySearchOptions.SectionName)
                .Get<AiFreeQuerySearchOptions>() ?? new AiFreeQuerySearchOptions();

            var freeQueryPermitLimit = configuration
                .GetValue<int?>($"{AiFreeQuerySearchOptions.SectionName}:{nameof(AiFreeQuerySearchOptions.RateLimitPermitLimit)}")
                ?? (isTestingEnvironment ? 10_000 : freeQueryOptions.RateLimitPermitLimit);

            options.AddPolicy(RateLimitPolicies.AiFreeQuerySearch, httpContext =>
                RateLimitPartition.GetFixedWindowLimiter(
                    partitionKey: httpContext.User.FindFirst(ClaimTypes.NameIdentifier)?.Value
                                  ?? httpContext.Connection.RemoteIpAddress?.ToString()
                                  ?? "unknown",
                    factory: _ => new FixedWindowRateLimiterOptions
                    {
                        PermitLimit = freeQueryPermitLimit,
                        Window = TimeSpan.FromSeconds(freeQueryOptions.RateLimitWindowSeconds),
                        QueueLimit = 0
                    }));

            // The sale agent (C42). Same shape a fourth time, and its own allowance because the
            // binding constraint here is not the money but the tokens-per-minute quota: one
            // conversation turn carries the whole transcript plus up to five turns of tool choosing,
            // measured at ~13 000 prompt tokens against a ceiling of 25 000 per minute. Sharing the
            // free query's allowance would let four conversations strangle the cheaper route.
            var agentOptions = configuration
                .GetSection(AiAgentAssistOptions.SectionName)
                .Get<AiAgentAssistOptions>() ?? new AiAgentAssistOptions();

            var agentPermitLimit = configuration
                .GetValue<int?>($"{AiAgentAssistOptions.SectionName}:{nameof(AiAgentAssistOptions.RateLimitPermitLimit)}")
                ?? (isTestingEnvironment ? 10_000 : agentOptions.RateLimitPermitLimit);

            options.AddPolicy(RateLimitPolicies.AiAgentAssist, httpContext =>
                RateLimitPartition.GetFixedWindowLimiter(
                    partitionKey: httpContext.User.FindFirst(ClaimTypes.NameIdentifier)?.Value
                                  ?? httpContext.Connection.RemoteIpAddress?.ToString()
                                  ?? "unknown",
                    factory: _ => new FixedWindowRateLimiterOptions
                    {
                        PermitLimit = agentPermitLimit,
                        Window = TimeSpan.FromSeconds(agentOptions.RateLimitWindowSeconds),
                        QueueLimit = 0
                    }));
        });

        // Add OpenAPI documentation with Scalar UI (skip in testing environments)
        var skipOpenApi = configuration.GetValue<bool>("Testing:SkipSwagger");
        if (!skipOpenApi)
        {
            services.AddOpenApi(); // .NET 10 built-in OpenAPI support
        }

        // Add CORS
        services.AddCors(options =>
        {
            options.AddPolicy("Development", policy =>
            {
                // Development CORS policy - allow specific origins with credentials
                var allowedOrigins = configuration.GetSection("Cors:AllowedOrigins").Get<string[]>() 
                    ?? new[] { "http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:5173" };
                
                policy.WithOrigins(allowedOrigins)
                      .AllowAnyMethod()
                      .AllowAnyHeader()
                      .AllowCredentials(); // Required for cookie-based auth
            });

            options.AddPolicy("Production", policy =>
            {
                // Configure production CORS policy based on environment
                var allowedOrigins = configuration.GetSection("Cors:AllowedOrigins").Get<string[]>() ?? Array.Empty<string>();
                policy.WithOrigins(allowedOrigins)
                      .AllowAnyMethod()
                      .AllowAnyHeader()
                      .AllowCredentials();
            });
        });

        // Add health checks
        services.AddHealthChecks();

        return services;
    }
}