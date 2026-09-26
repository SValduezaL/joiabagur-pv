using System.Net;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Polly;
using Polly.Timeout;

namespace JoiabagurPV.Application.Extensions;

/// <summary>
/// Registers the jbg-ai gateway: options with start-up validation, the service token factory
/// and the named HTTP client carrying the resilience pipeline.
/// </summary>
public static class AiGatewayServiceCollectionExtensions
{
    /// <summary>
    /// Adds the AI gateway client and validates its configuration during host start-up.
    /// </summary>
    public static IServiceCollection AddAiGateway(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(configuration);

        var section = configuration.GetSection(AiGatewayOptions.SectionName);

        // A disabled gateway registers nothing and validates nothing: an unused integration
        // must not be able to stop the API from starting.
        if (!section.GetValue("Enabled", true))
        {
            return services;
        }

        services
            .AddOptions<AiGatewayOptions>()
            .Bind(section)
            // Absolute is not enough: Uri.TryCreate accepts "localhost:8001" as an absolute URI
            // whose scheme is "localhost". That is precisely the typo someone makes in production
            // configuration, so the scheme is checked explicitly.
            .Validate(
                o => Uri.TryCreate(o.BaseUrl, UriKind.Absolute, out var uri)
                     && (uri.Scheme == Uri.UriSchemeHttp || uri.Scheme == Uri.UriSchemeHttps),
                $"{AiGatewayOptions.SectionName}:BaseUrl must be an absolute http or https URI (for example http://localhost:8001).")
            .Validate(
                o => !string.IsNullOrWhiteSpace(o.JwtSecret),
                $"{AiGatewayOptions.SectionName}:JwtSecret is not configured. It must match the JWT_SECRET of the jbg-ai service literally.")
            .Validate(
                o => o.JwtSecret.Length >= AiGatewayOptions.MinimumSecretLength,
                $"{AiGatewayOptions.SectionName}:JwtSecret is too short for HS256; at least {AiGatewayOptions.MinimumSecretLength} characters are required.")
            .Validate(
                o => o.TokenTtlSeconds > 0 && o.RetrievalTimeoutMs > 0 && o.AssistTimeoutMs > 0
                     && o.EnrichTimeoutMs > 0 && o.HealthTimeoutMs > 0 && o.AgentTimeoutMs > 0,
                $"{AiGatewayOptions.SectionName} time-to-live and time budgets must be positive.")
            // The outer budget must cover the worst case the AI service declares inside. Checked
            // here so that relation is something start-up verifies instead of something somebody
            // has to remember the day the budget is tuned down.
            .Validate(
                o => o.AssistTimeoutMs >= AiGatewayOptions.MinimumAssistTimeoutMs,
                $"{AiGatewayOptions.SectionName}:AssistTimeoutMs must be at least {AiGatewayOptions.MinimumAssistTimeoutMs} ms: "
                + "the worst case jbg-ai declares for the provider calls of one sale assistance is "
                + "MAX_PITCH_PROVIDER_CALLS × PITCH_TIMEOUT_SECONDS = 2 × 4 s (ai-service/src/jbg_ai/assist/constants.py). "
                + "A shorter budget discards answers the service was still entitled to deliver.")
            // Same relation, one route along, and here the argument is sharper: exceeding the
            // service's deadline is a DEGRADATION there — the evidence gathered is served and the
            // answer says the clock stopped it — so a budget under the ceiling replaces a partial
            // answer the service already paid for with nothing at all.
            .Validate(
                o => o.AgentTimeoutMs >= AiGatewayOptions.MinimumAgentTimeoutMs,
                $"{AiGatewayOptions.SectionName}:AgentTimeoutMs must be at least {AiGatewayOptions.MinimumAgentTimeoutMs} ms: "
                + "that is the wall-clock ceiling jbg-ai gives one agent request, "
                + "AGENT_DEADLINE_SECONDS = 15 s (ai-service/src/jbg_ai/assist/constants.py), and this "
                + "budget has to cover it plus the network. Fitting it to the maximum latency observed "
                + "in measurement is the mistake to avoid: it cuts a request Python has already paid "
                + "for in full.")
            // ValidateOnStart is the whole point. Without it the check is lazy and would surface
            // inside a request instead of at boot, which is the failure mode being removed here.
            .ValidateOnStart();

        var options = section.Get<AiGatewayOptions>() ?? new AiGatewayOptions();

        services.TryAddTimeProvider();
        services.AddScoped<IAiServiceTokenFactory, AiServiceTokenFactory>();
        services.AddScoped<IAiGatewayClient, AiGatewayClient>();

        services
            .AddHttpClient(AiGatewayClient.RetrievalClientName, client =>
            {
                client.BaseAddress = new Uri(options.BaseUrl);

                // The pipeline owns the time budget. Leaving HttpClient's own timeout in play
                // would race it and surface as a cancellation the retry cannot classify.
                client.Timeout = Timeout.InfiniteTimeSpan;
            })
            .AddResilienceHandler("ai-retrieval-pipeline", builder =>
            {
                // Outermost first. Retry wraps the breaker, which wraps the per-attempt timeout,
                // so each attempt gets the full budget and the breaker sees each attempt.
                builder.AddRetry(new HttpRetryStrategyOptions
                {
                    MaxRetryAttempts = 1,
                    Delay = TimeSpan.FromMilliseconds(100),
                    BackoffType = DelayBackoffType.Constant,
                    UseJitter = false,
                    ShouldHandle = args => ValueTask.FromResult(IsRetryable(args.Outcome)),
                    OnRetry = _ =>
                    {
                        AiGatewayAttemptTracker.RecordRetry();
                        return default;
                    }
                });

                builder.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
                {
                    FailureRatio = options.BreakerFailureRatio,
                    MinimumThroughput = options.BreakerMinimumThroughput,
                    SamplingDuration = TimeSpan.FromSeconds(options.BreakerSamplingDurationSeconds),
                    BreakDuration = TimeSpan.FromSeconds(options.BreakerBreakDurationSeconds),
                    ShouldHandle = args => ValueTask.FromResult(IsRetryable(args.Outcome))
                });

                builder.AddTimeout(TimeSpan.FromMilliseconds(options.RetrievalTimeoutMs));
            });

        services
            .AddHttpClient(AiGatewayClient.EnrichClientName, client =>
            {
                client.BaseAddress = new Uri(options.BaseUrl);
                client.Timeout = Timeout.InfiniteTimeSpan;
            })
            .AddResilienceHandler("ai-enrich-pipeline", builder =>
            {
                // No retry, deliberately. A second attempt at a structured extraction spends the
                // model budget again with no reason to expect a different answer, and the
                // delivery commits to the AI cost being instrumented and defensible. A failed
                // batch is re-run by an administrator who decided to, not by a policy.
                builder.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
                {
                    FailureRatio = options.BreakerFailureRatio,
                    MinimumThroughput = options.BreakerMinimumThroughput,
                    SamplingDuration = TimeSpan.FromSeconds(options.BreakerSamplingDurationSeconds),
                    BreakDuration = TimeSpan.FromSeconds(options.BreakerBreakDurationSeconds),
                    ShouldHandle = args => ValueTask.FromResult(IsRetryable(args.Outcome))
                });

                builder.AddTimeout(TimeSpan.FromMilliseconds(options.EnrichTimeoutMs));
            });

        // The health client (C17). NO resilience handler, and that is the entire point of it
        // being a separate registration rather than a third call on the retrieval client:
        //
        //   * No circuit breaker. The probe exists to diagnose the system when the main path is
        //     already failing. Sharing retrieval's breaker would make it decline to answer at
        //     exactly the moment an administrator opens the dashboard to find out why.
        //   * No retry. A human refreshing a card is the retry, and each attempt costs them a
        //     wait.
        //
        // The budget is therefore the client's own timeout, with no pipeline to race against it.
        services
            .AddHttpClient(AiGatewayClient.HealthClientName, client =>
            {
                client.BaseAddress = new Uri(options.BaseUrl);
                client.Timeout = TimeSpan.FromMilliseconds(options.HealthTimeoutMs);
            });

        // The generative route (C34). Its own client and its own breaker state, on purpose: a
        // slow language model must not open the retrieval circuit and push the caller onto its
        // lexical fallback for a service that is answering correctly. Substitutes do NOT come
        // here — they are a retrieval route, embed nothing and ride on ai-retrieval.
        services
            .AddHttpClient(AiGatewayClient.AssistClientName, client =>
            {
                client.BaseAddress = new Uri(options.BaseUrl);
                client.Timeout = Timeout.InfiniteTimeSpan;
            })
            .AddResilienceHandler("ai-assist-pipeline", builder =>
            {
                // One retry, and only for a connection that never opened. A timeout is NOT
                // retried here, unlike retrieval: the service may already have spent its
                // provider calls, and a second attempt doubles both the wait at the counter —
                // twenty seconds — and the paid calls. A 5xx is not retried either, for the same
                // reason. A connection refused is the one failure where the request is known not
                // to have left, so nothing was spent.
                builder.AddRetry(new HttpRetryStrategyOptions
                {
                    MaxRetryAttempts = 1,
                    Delay = TimeSpan.FromMilliseconds(100),
                    BackoffType = DelayBackoffType.Constant,
                    UseJitter = false,
                    ShouldHandle = args => ValueTask.FromResult(IsConnectionNeverOpened(args.Outcome)),
                    OnRetry = _ =>
                    {
                        AiGatewayAttemptTracker.RecordRetry();
                        return default;
                    }
                });

                // Counts the same transient conditions as the retrieval breaker. A 200 the
                // service degraded internally — no argument because the provider failed — is not
                // a failure: Python degraded, and the breaker protects from Python not answering.
                builder.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
                {
                    FailureRatio = options.BreakerFailureRatio,
                    MinimumThroughput = options.BreakerMinimumThroughput,
                    SamplingDuration = TimeSpan.FromSeconds(options.BreakerSamplingDurationSeconds),
                    BreakDuration = TimeSpan.FromSeconds(options.BreakerBreakDurationSeconds),
                    ShouldHandle = args => ValueTask.FromResult(IsRetryable(args.Outcome))
                });

                builder.AddTimeout(TimeSpan.FromMilliseconds(options.AssistTimeoutMs));
            });

        // The sale agent (C42). Its own client, its own budget and its own breaker state, for the
        // reason the generative route got its own and one more of its own: the agent's MEDIAN
        // latency is of the order of the total the generative route declares as its ceiling, so
        // sharing that client would cut a large share of agent requests, and sharing its breaker
        // would let a slow conversation open the circuit of a route that is answering correctly.
        services
            .AddHttpClient(AiGatewayClient.AgentClientName, client =>
            {
                client.BaseAddress = new Uri(options.BaseUrl);
                client.Timeout = Timeout.InfiniteTimeSpan;
            })
            .AddResilienceHandler("ai-agent-pipeline", builder =>
            {
                // One retry, and only for a connection that never opened — the assist policy
                // exactly, and the argument is stronger here. A timeout is NOT retried: the loop
                // may already have spent up to five turns of provider calls plus the argument, so a
                // second attempt doubles both the wait at the counter — thirty-six seconds — and the
                // paid calls. A 5xx is not retried for the same reason. A connection refused is the
                // one failure where the request is known not to have left, so nothing was spent.
                builder.AddRetry(new HttpRetryStrategyOptions
                {
                    MaxRetryAttempts = 1,
                    Delay = TimeSpan.FromMilliseconds(100),
                    BackoffType = DelayBackoffType.Constant,
                    UseJitter = false,
                    ShouldHandle = args => ValueTask.FromResult(IsConnectionNeverOpened(args.Outcome)),
                    OnRetry = _ =>
                    {
                        AiGatewayAttemptTracker.RecordRetry();
                        return default;
                    }
                });

                // Counts conditions of TRANSPORT only, and the omission is the decision rather than
                // a limitation of where this code sits.
                //
                // This route does not answer with a server error when its provider falls: it answers
                // 200, reporting `stop_reason = fallo_proveedor` in a closed vocabulary. The same is
                // true of `sin_cliente`, when no agent credential is configured, and of the five
                // budget reasons. `IsRetryable` receives an `Outcome<HttpResponseMessage>` and does
                // not read the body, so none of those is visible here — but that is convenient, not
                // the reason. The reason is that what a breaker protects against is the AI service
                // not answering. A breaker that counted a degradation the service answered WITH
                // would open over a route working exactly as designed; one that ignored a transport
                // failure would lose the only signal that the service is down.
                //
                // Two alternatives were considered and rejected. A handler that read the body would
                // have to buffer the response, parse the JSON twice and couple the transport to the
                // contract's closed vocabulary. A domain breaker in the application service would be
                // correct in layering and UNREACHABLE in practice: at ~13 000 tokens per request
                // against a 25 000 tokens-per-minute quota the system admits about ONE REQUEST PER
                // MINUTE, so a sampling window of 30 s expires long before MinimumThroughput
                // accumulates. The deferred entry of C32b asking for this is closed by refutation.
                //
                // The degradation is instrumented instead — a metric and a log line, in
                // `AiGatewayClient` — so its rate stays observable without the breaker acting on it.
                // What tells a screen the agent is unavailable is the availability probe, which costs
                // no quota and no provider call.
                builder.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions
                {
                    FailureRatio = options.BreakerFailureRatio,
                    MinimumThroughput = options.BreakerMinimumThroughput,
                    SamplingDuration = TimeSpan.FromSeconds(options.BreakerSamplingDurationSeconds),
                    BreakDuration = TimeSpan.FromSeconds(options.BreakerBreakDurationSeconds),
                    ShouldHandle = args => ValueTask.FromResult(IsRetryable(args.Outcome))
                });

                builder.AddTimeout(TimeSpan.FromMilliseconds(options.AgentTimeoutMs));
            });

        return services;
    }

    /// <summary>
    /// The only failure the generative client retries: the connection was never established, so
    /// the request did not leave and no provider call was spent.
    /// </summary>
    private static bool IsConnectionNeverOpened(Outcome<HttpResponseMessage> outcome) =>
        outcome.Exception is HttpRequestException { HttpRequestError: HttpRequestError.ConnectionError };

    /// <summary>
    /// Transient conditions worth one more attempt, and the same set the breaker counts as
    /// failures.
    /// </summary>
    /// <remarks>
    /// A whitelist, never "any server error". HTTP 501 is excluded because jbg-ai uses it for a
    /// route whose implementation arrives in a later change: retrying spends the budget with no
    /// possibility of success, and counting it as a health failure would open the circuit on a
    /// service that is perfectly healthy. HTTP 401 is excluded for the same reason — it is
    /// configuration, and no number of attempts fixes a mismatched secret.
    /// </remarks>
    private static bool IsRetryable(Outcome<HttpResponseMessage> outcome)
    {
        if (outcome.Exception is HttpRequestException or TimeoutRejectedException)
        {
            return true;
        }

        var status = outcome.Result?.StatusCode;
        if (status is null)
        {
            return false;
        }

        if (status == HttpStatusCode.RequestTimeout)
        {
            return true;
        }

        return (int)status >= 500 && status != HttpStatusCode.NotImplemented;
    }

    private static IServiceCollection TryAddTimeProvider(this IServiceCollection services)
    {
        if (services.All(d => d.ServiceType != typeof(TimeProvider)))
        {
            services.AddSingleton(TimeProvider.System);
        }

        return services;
    }
}
