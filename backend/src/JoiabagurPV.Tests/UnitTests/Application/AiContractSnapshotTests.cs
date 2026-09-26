using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Tests.TestHelpers;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// The reciprocal of the Python snapshot test.
/// </summary>
/// <remarks>
/// jbg-ai already breaks its own build when the contract drifts. Without this, the .NET build
/// stays green and the drift surfaces at runtime as a silently null value — the worst possible
/// place to find out. With both guards in place, renegotiating the contract breaks both builds,
/// which is exactly what turns drift into an explicit conversation.
/// </remarks>
public class AiContractSnapshotTests
{
    private static readonly JsonSerializerOptions Wire = AiGatewaySerialization.Options;

    public static TheoryData<Type, string> ModelToSchema => new()
    {
        { typeof(AiSearchRequest), "RetrievalRequest" },
        { typeof(AiSearchFilters), "RetrievalFilters" },
        { typeof(AiSearchResult), "RetrievalResult" },
        { typeof(AiSearchResponse), "RetrievalResponse" },
        { typeof(AiDebugInfo), "DebugInfo" },
        { typeof(AiEnrichProductInput), "EnrichProductInput" },
        { typeof(AiEnrichRequest), "EnrichRequest" },
        { typeof(AiProposedText), "ProposedText" },
        { typeof(AiProposedList), "ProposedList" },
        { typeof(AiProposedProfile), "ProposedProfile" },
        { typeof(AiEnrichResponse), "EnrichResponse" },
        { typeof(AiUsage), "Usage" },
        { typeof(AiAssistSaleRequest), "AssistRequest" },
        { typeof(AiAssistSaleResponse), "AssistResponse" },
        { typeof(AiAssistGroup), "AssistGroup" },
        { typeof(AiAssistGroupMember), "AssistGroupMember" },
        { typeof(AiCitation), "Citation" },
        { typeof(AiSubstitutesRequest), "SubstitutesRequest" },
        { typeof(AiSubstitutesResponse), "SubstitutesResponse" },
        { typeof(AiSubstituteResult), "SubstituteResult" },
        { typeof(AiSimilaritySignals), "SimilaritySignals" },

        // The sale agent (C42). **These five are the only thing that guards the wire names of a
        // route nobody had ever called.** The client's own tests deserialize a hand-written body, so
        // a property misspelled on both sides — `toolCallsUsed` where the contract says
        // `tool_calls_used` — would pass them and arrive as a silent null in production, which is
        // precisely the failure this whole class exists to move to build time.
        { typeof(AiAgentTurn), "AgentTurn" },
        { typeof(AiAssistAgentRequest), "AgentAssistRequest" },
        { typeof(AiAssistAgentResponse), "AgentAssistResponse" },
        { typeof(AiAssistAgentGroup), "AgentAssistGroup" },
        { typeof(AiAgentUsage), "AgentUsage" },
        { typeof(AiAgentTraceIteration), "AgentTraceIteration" },
        { typeof(AiAgentTraceTool), "AgentTraceTool" }
    };

    [Theory]
    [MemberData(nameof(ModelToSchema))]
    public void Dtos_MatchCommittedOpenApiSchema(Type model, string schemaName)
    {
        var schema = LoadSchema(schemaName);

        foreach (var property in model.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            var wireName = Wire.PropertyNamingPolicy!.ConvertName(property.Name);

            schema.TryGetProperty(wireName, out var declared).Should().BeTrue(
                "{0}.{1} serializes as '{2}', which must exist in schema {3} of the committed contract",
                model.Name, property.Name, wireName, schemaName);

            IsNullableInContract(declared).Should().Be(
                IsNullableInModel(property),
                "nullability of '{0}' must match between {1} and schema {2}: the contract returns an " +
                "explicit null where a value is unknown, and a non-nullable member would hide that",
                wireName, model.Name, schemaName);
        }
    }

    /// <summary>
    /// The request model deliberately omits pos_id: the contract accepts it and ignores it,
    /// because scope comes from the token. Sending it would suggest the body carries authority.
    /// </summary>
    [Fact]
    public void SearchRequest_OmitsPosIdEvenThoughTheContractAcceptsIt()
    {
        LoadSchema("RetrievalRequest").TryGetProperty("pos_id", out _).Should().BeTrue(
            "the contract still declares it");

        typeof(AiSearchRequest).GetProperties()
            .Select(p => Wire.PropertyNamingPolicy!.ConvertName(p.Name))
            .Should().NotContain("pos_id");
    }

    /// <summary>
    /// The twin of the retrieval guard for sale assistance, asserted on the serialized payload
    /// rather than on the property list: what matters is what leaves the process.
    /// </summary>
    [Fact]
    public void AssistSaleRequest_Serialization_OmitsPosId()
    {
        LoadSchema("AssistRequest").TryGetProperty("pos_id", out _).Should().BeTrue(
            "the contract still declares it");

        var json = JsonSerializer.Serialize(
            new AiAssistSaleRequest { ProductId = Guid.NewGuid().ToString(), Query = "¿se puede mojar?" },
            Wire);

        using var document = JsonDocument.Parse(json);
        var names = document.RootElement.EnumerateObject().Select(p => p.Name).ToList();

        names.Should().NotContain("pos_id", "the scope travels in the token, never in the body");
        names.Should().BeEquivalentTo(["product_id", "query", "filters"],
            "the wire names are snake_case, and `filters` travels like it does on the "
            + "substitutes request: declared with a default in the contract, so non-nullable "
            + "here and always serialized rather than omitted");
    }

    [Fact]
    public void SubstitutesRequest_Serialization_OmitsPosId()
    {
        LoadSchema("SubstitutesRequest").TryGetProperty("pos_id", out _).Should().BeTrue(
            "the contract still declares it");

        var json = JsonSerializer.Serialize(
            new AiSubstitutesRequest { ProductId = Guid.NewGuid().ToString(), TopK = 20, Reason = "sin_stock" },
            Wire);

        using var document = JsonDocument.Parse(json);
        var names = document.RootElement.EnumerateObject().Select(p => p.Name).ToList();

        names.Should().NotContain("pos_id", "the scope travels in the token, never in the body");
        names.Should().BeEquivalentTo(["product_id", "top_k", "reason", "filters"]);
    }

    /// <summary>
    /// Provenance is the field the whole hybrid review policy turns on, so it is asserted by
    /// name rather than left to the generic property sweep.
    /// </summary>
    /// <remarks>
    /// If a later renegotiation dropped `source` from a proposed value, the sweep above would
    /// still pass — it only checks that .NET properties exist in the contract, not the reverse.
    /// The review policy would then silently treat every sensitive field as inferred and send
    /// the whole catalog to a review queue nobody has time for.
    /// </remarks>
    [Theory]
    [InlineData("ProposedText")]
    [InlineData("ProposedList")]
    public void ProposedValues_DeclareProvenanceInTheContract(string schemaName)
    {
        var schema = LoadSchema(schemaName);

        schema.TryGetProperty("source", out var source).Should().BeTrue(
            "without per-field provenance the hybrid review policy cannot distinguish a value a "
            + "rule produced from one a model inferred, which is the whole of decision 5");

        source.GetProperty("enum").EnumerateArray()
            .Select(value => value.GetString())
            .Should().BeEquivalentTo(["rule", "inferred"]);
    }

    private static JsonElement LoadSchema(string schemaName)
    {
        var path = RepositoryRoot.Resolve("ai-service", "openapi.json");

        File.Exists(path).Should().BeTrue("the committed contract must be readable at {0}", path);

        using var document = JsonDocument.Parse(File.ReadAllText(path));

        return document.RootElement
            .GetProperty("components")
            .GetProperty("schemas")
            .GetProperty(schemaName)
            .GetProperty("properties")
            .Clone();
    }

    /// <summary>
    /// Pydantic emits an optional field as anyOf[..., {"type": "null"}].
    /// </summary>
    private static bool IsNullableInContract(JsonElement property)
    {
        if (property.TryGetProperty("anyOf", out var anyOf))
        {
            return anyOf.EnumerateArray().Any(o =>
                o.TryGetProperty("type", out var t) && t.GetString() == "null");
        }

        return property.TryGetProperty("type", out var type) && type.GetString() == "null";
    }

    private static bool IsNullableInModel(PropertyInfo property)
    {
        var type = property.PropertyType;

        if (Nullable.GetUnderlyingType(type) is not null)
        {
            return true;
        }

        if (type.IsValueType)
        {
            return false;
        }

        return new NullabilityInfoContext().Create(property).WriteState == NullabilityState.Nullable;
    }
}
