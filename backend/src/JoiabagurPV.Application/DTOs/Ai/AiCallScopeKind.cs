namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// What kind of jbg-ai route a call scope may be used on.
/// </summary>
/// <remarks>
/// Exists so the refusal can be made by the client rather than left to the reader of a nullable
/// point of sale. A null identifier says "there is none"; this says "and that is deliberate,
/// for this family of routes" — which is what makes sending it to retrieval a bug the client can
/// name instead of a null reference it happens to trip over.
/// </remarks>
public enum AiCallScopeKind
{
    /// <summary>Scoped to one point of sale: retrieval, sale assistance, inventory.</summary>
    PointOfSale = 1,

    /// <summary>Scoped to the whole catalog: enrichment, index synchronization.</summary>
    Catalog = 2,

    /// <summary>
    /// A search deliberately covering every point of sale: catalog retrieval and sale
    /// assistance only.
    /// </summary>
    /// <remarks>
    /// <strong>Not a relaxation of <see cref="PointOfSale"/> and not a synonym of
    /// <see cref="Catalog"/>.</strong> It carries no point of sale, like the catalog scope, but
    /// it is a different intent and the client treats it differently: the catalog scope is
    /// refused by every point-of-sale route, while this one is accepted by the two that can
    /// answer without a shop and refused by the rest. Collapsing the two would make
    /// enrichment's scope usable for a search, which is the leak the kinds exist to prevent.
    /// </remarks>
    AllPointsOfSale = 3
}
