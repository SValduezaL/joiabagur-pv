using System.Reflection;
using FluentAssertions;
using JoiabagurPV.Application.DTOs.Ai;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// The scope is the guard that stops a sentinel point of sale from ever reaching the
/// retriever's hard filter. These tests pin that guard.
/// </summary>
public class AiCallScopeTests
{
    private static readonly Guid AnyUser = Guid.NewGuid();
    private static readonly Guid AnyPointOfSale = Guid.NewGuid();
    private const string AnyRole = "Operator";

    [Fact]
    public void ForPointOfSale_WithValidArguments_BuildsScope()
    {
        var scope = AiCallScope.ForPointOfSale(AnyUser, AnyRole, AnyPointOfSale);

        scope.UserId.Should().Be(AnyUser);
        scope.Role.Should().Be(AnyRole);
        scope.PointOfSaleId.Should().Be(AnyPointOfSale);
    }

    [Fact]
    public void ForPointOfSale_WhenPointOfSaleIsEmpty_ThrowsArgumentException()
    {
        var act = () => AiCallScope.ForPointOfSale(AnyUser, AnyRole, Guid.Empty);

        act.Should().Throw<ArgumentException>()
            .WithParameterName("pointOfSaleId");
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public void ForPointOfSale_WhenRoleIsBlank_ThrowsArgumentException(string role)
    {
        var act = () => AiCallScope.ForPointOfSale(AnyUser, role, AnyPointOfSale);

        act.Should().Throw<ArgumentException>()
            .WithParameterName("role");
    }

    [Fact]
    public void ForPointOfSale_WhenUserIsEmpty_ThrowsArgumentException()
    {
        var act = () => AiCallScope.ForPointOfSale(Guid.Empty, AnyRole, AnyPointOfSale);

        act.Should().Throw<ArgumentException>()
            .WithParameterName("userId");
    }

    /// <summary>
    /// Guards the reason the type is a sealed class and not a record struct: a struct would
    /// always have a `default` value carrying an empty point of sale, which is exactly the
    /// state the factory exists to prevent.
    /// </summary>
    [Fact]
    public void AiCallScope_ExposesNoPublicConstructor()
    {
        typeof(AiCallScope)
            .GetConstructors()
            .Should().BeEmpty("the two static factories must be the only ways to build a scope");

        typeof(AiCallScope).IsValueType
            .Should().BeFalse("a value type would always have a default instance with an empty point of sale");
    }

    [Fact]
    public void ForCatalog_CarriesNoPointOfSale()
    {
        var scope = AiCallScope.ForCatalog(AnyUser, AnyRole);

        scope.PointOfSaleId.Should().BeNull(
            "enriching the catalog belongs to no point of sale, and a null cannot be mistaken "
            + "for one the way a sentinel value could");
        scope.Kind.Should().Be(AiCallScopeKind.Catalog);
        scope.UserId.Should().Be(AnyUser);
        scope.Role.Should().Be(AnyRole);
    }

    [Fact]
    public void ForCatalog_WhenRoleIsBlank_ThrowsArgumentException()
    {
        var act = () => AiCallScope.ForCatalog(AnyUser, "  ");

        act.Should().Throw<ArgumentException>()
            .WithParameterName("role");
    }

    [Fact]
    public void ForCatalog_WhenUserIsEmpty_ThrowsArgumentException()
    {
        var act = () => AiCallScope.ForCatalog(Guid.Empty, AnyRole);

        act.Should().Throw<ArgumentException>()
            .WithParameterName("userId");
    }

    [Fact]
    public void ForPointOfSale_IsMarkedAsPointOfSaleScoped()
    {
        var scope = AiCallScope.ForPointOfSale(AnyUser, AnyRole, AnyPointOfSale);

        scope.Kind.Should().Be(AiCallScopeKind.PointOfSale);
    }

    /// <summary>
    /// The catalog scope must remain a second scope, never a third construction path that
    /// happens to produce a point-of-sale one without a point of sale.
    /// </summary>
    /// <summary>
    /// C40 adds the third and the count moves with it, deliberately: this test exists so that
    /// a fourth path cannot be added without somebody deciding to.
    /// </summary>
    [Fact]
    public void AiCallScope_ExposesExactlyThreeConstructionPaths()
    {
        typeof(AiCallScope)
            .GetMethods(BindingFlags.Public | BindingFlags.Static)
            .Where(method => method.ReturnType == typeof(AiCallScope))
            .Select(method => method.Name)
            .Should().BeEquivalentTo(["ForPointOfSale", "ForCatalog", "ForAllPointsOfSale"]);

        typeof(AiCallScope)
            .GetConstructors(BindingFlags.Public | BindingFlags.Instance)
            .Should().BeEmpty("a public constructor would be a fourth path with no guard on it");
    }

    [Fact]
    public void ForAllPointsOfSale_CarriesNoPointOfSale()
    {
        var scope = AiCallScope.ForAllPointsOfSale(AnyUser, AnyRole);

        scope.UserId.Should().Be(AnyUser);
        scope.Role.Should().Be(AnyRole);
        scope.PointOfSaleId.Should().BeNull(
            "the absence of a point of sale is what makes the prefilter not apply; a sentinel "
            + "would reach the retriever's only hard filter and match everything");
    }

    /// <summary>
    /// Same fields, different kind, and that is the whole reason the kind exists: collapsing
    /// them would make enrichment's scope usable for a search.
    /// </summary>
    [Fact]
    public void ForAllPointsOfSale_IsDistinguishableFromACatalogScope()
    {
        var everyShop = AiCallScope.ForAllPointsOfSale(AnyUser, AnyRole);
        var catalog = AiCallScope.ForCatalog(AnyUser, AnyRole);

        everyShop.PointOfSaleId.Should().Be(catalog.PointOfSaleId);
        everyShop.Kind.Should().Be(AiCallScopeKind.AllPointsOfSale);
        catalog.Kind.Should().Be(AiCallScopeKind.Catalog);
        everyShop.Kind.Should().NotBe(catalog.Kind);
    }

    [Theory]
    [InlineData("")]
    [InlineData("   ")]
    public void ForAllPointsOfSale_WhenRoleIsBlank_ThrowsArgumentException(string role)
    {
        var act = () => AiCallScope.ForAllPointsOfSale(AnyUser, role);

        act.Should().Throw<ArgumentException>();
    }

    [Fact]
    public void ForAllPointsOfSale_WhenUserIsEmpty_ThrowsArgumentException()
    {
        var act = () => AiCallScope.ForAllPointsOfSale(Guid.Empty, AnyRole);

        act.Should().Throw<ArgumentException>();
    }
}
