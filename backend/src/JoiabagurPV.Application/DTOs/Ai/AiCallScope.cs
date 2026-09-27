namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// Caller identity and, when the route has one, point-of-sale scope carried into every jbg-ai call.
/// </summary>
/// <remarks>
/// <para>
/// This type <em>authorises nothing</em>. Whoever builds a scope has already validated that
/// the user is assigned to that point of sale, against <c>UserPointOfSale</c>. The client
/// only transports it.
/// </para>
/// <para>
/// There are exactly three construction paths and no fourth. <see cref="ForPointOfSale"/> requires
/// a concrete point of sale: from C22 onward the <c>pos_id</c> claim becomes the retriever's only
/// hard filter, so a sentinel value such as "*" or "system" reaching it would be a cross-POS leak
/// wearing a convenience-parameter costume. <see cref="ForCatalog"/> carries none at all, for the
/// routes that operate over the whole catalog — enrichment, and later index synchronization — and
/// therefore belong to no point of sale. <see cref="ForAllPointsOfSale"/> carries none either, for
/// a search the operator deliberately spread over every shop.
/// </para>
/// <para>
/// Neither of the other two is a relaxation of the first: they are different scopes. The catalog
/// one is <em>refused</em> by every point-of-sale operation of the client; the every-shop one is
/// refused by all of them except catalog retrieval and sale assistance, which are the two that
/// can answer without a shop. Making the leaking state unconstructible is cheaper than asking
/// people not to write it; refusing a scope where a point of sale is mandatory is what keeps that
/// guarantee once the state exists.
/// </para>
/// <para>
/// <see cref="ForCatalog"/> and <see cref="ForAllPointsOfSale"/> hold the same fields and are
/// still two kinds, on purpose: collapsing them would make enrichment's scope usable for a
/// search. <see cref="Kind"/> is the only thing that tells them apart, which is exactly why it
/// exists.
/// </para>
/// <para>
/// A sealed class rather than a record struct on purpose: every struct has an implicit
/// <c>default</c> value, which would be a scope with neither kind nor identity and would defeat
/// the guarantee above. A private constructor on a class has no such hole.
/// </para>
/// </remarks>
public sealed class AiCallScope
{
    private AiCallScope(Guid userId, string role, Guid? pointOfSaleId, AiCallScopeKind kind)
    {
        UserId = userId;
        Role = role;
        PointOfSaleId = pointOfSaleId;
        Kind = kind;
    }

    /// <summary>Identifier of the user on whose behalf the call is made.</summary>
    public Guid UserId { get; }

    /// <summary>Role of that user.</summary>
    public string Role { get; }

    /// <summary>
    /// Point of sale the call is scoped to, or null for a catalog-wide scope and for a search
    /// spread over every point of sale. <see cref="Kind"/> is what tells those two apart.
    /// </summary>
    /// <remarks>
    /// Nullable rather than a sentinel: a null cannot be mistaken for a point of sale, and it
    /// makes the token factory omit the claim entirely instead of emitting an empty one, which
    /// the service would reject anyway.
    /// </remarks>
    public Guid? PointOfSaleId { get; }

    /// <summary>What kind of route this scope may be used on.</summary>
    public AiCallScopeKind Kind { get; }

    /// <summary>
    /// Builds a scope for a concrete point of sale.
    /// </summary>
    /// <param name="userId">User the call is made for. Must not be empty.</param>
    /// <param name="role">Role of that user. Must not be blank.</param>
    /// <param name="pointOfSaleId">Point of sale the call is scoped to. Must not be empty.</param>
    /// <exception cref="ArgumentException">Any argument is empty or blank.</exception>
    public static AiCallScope ForPointOfSale(Guid userId, string role, Guid pointOfSaleId)
    {
        RequireIdentity(userId, role);

        if (pointOfSaleId == Guid.Empty)
        {
            throw new ArgumentException(
                "A point-of-sale gateway call scope requires a concrete point of sale. There is no scope without one.",
                nameof(pointOfSaleId));
        }

        return new AiCallScope(userId, role, pointOfSaleId, AiCallScopeKind.PointOfSale);
    }

    /// <summary>
    /// Builds a scope for a catalog-wide call, which belongs to no point of sale.
    /// </summary>
    /// <param name="userId">User the call is made for. Must not be empty.</param>
    /// <param name="role">Role of that user. Must not be blank.</param>
    /// <exception cref="ArgumentException">Any argument is empty or blank.</exception>
    public static AiCallScope ForCatalog(Guid userId, string role)
    {
        RequireIdentity(userId, role);

        return new AiCallScope(userId, role, pointOfSaleId: null, AiCallScopeKind.Catalog);
    }

    /// <summary>
    /// Builds a scope for a search that deliberately covers every point of sale.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <strong>The absence of a point of sale, never a wildcard.</strong> That distinction is the
    /// whole safety of this path: an absent <c>pos_id</c> claim makes the availability prefilter
    /// <em>not apply</em>, and fails closed on every route that requires the claim. A sentinel
    /// would instead reach the retriever's only hard filter and match everything, which is the
    /// cross-point-of-sale leak the other two paths exist to prevent.
    /// </para>
    /// <para>
    /// Like the other two, this authorises nothing. Whoever builds it has already checked that the
    /// caller may search across every point of sale — which operators and administrators may,
    /// because the stock breakdown of a product is already readable across every shop by any
    /// authenticated caller, so a search that spans them discloses nothing new.
    /// </para>
    /// </remarks>
    /// <param name="userId">User the call is made for. Must not be empty.</param>
    /// <param name="role">Role of that user. Must not be blank.</param>
    /// <exception cref="ArgumentException">Any argument is empty or blank.</exception>
    public static AiCallScope ForAllPointsOfSale(Guid userId, string role)
    {
        RequireIdentity(userId, role);

        return new AiCallScope(userId, role, pointOfSaleId: null, AiCallScopeKind.AllPointsOfSale);
    }

    private static void RequireIdentity(Guid userId, string role)
    {
        if (userId == Guid.Empty)
        {
            throw new ArgumentException("A gateway call scope requires a user.", nameof(userId));
        }

        if (string.IsNullOrWhiteSpace(role))
        {
            throw new ArgumentException("A gateway call scope requires a role.", nameof(role));
        }
    }
}
