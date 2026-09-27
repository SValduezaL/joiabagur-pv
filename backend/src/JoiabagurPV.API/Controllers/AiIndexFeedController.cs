using JoiabagurPV.API.Filters;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace JoiabagurPV.API.Controllers;

/// <summary>
/// HTTP pull surface for catalog and POS indexation. Authenticated only by
/// <c>X-Index-Feed-Key</c>. There is no <c>[Authorize]</c> on purpose: a user JWT must not
/// open these routes.
/// </summary>
[ApiController]
[Route("api/ai/index-feed")]
[IndexFeedKey]
public class AiIndexFeedController : ControllerBase
{
    private readonly IIndexFeedService _feedService;

    public AiIndexFeedController(IIndexFeedService feedService)
    {
        _feedService = feedService;
    }

    /// <summary>Catalog feed, page size 50, keyset on <c>(watermark, productId)</c>.</summary>
    [HttpGet("catalog")]
    [ProducesResponseType(typeof(IndexFeedPageDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<IndexFeedPageDto>> GetCatalog(
        [FromQuery] DateTime? since,
        [FromQuery] Guid? sinceId,
        CancellationToken cancellationToken)
    {
        var page = await _feedService.GetCatalogPageAsync(since, sinceId, cancellationToken);
        return Ok(page);
    }

    /// <summary>
    /// Sparse POS availability feed, page size 200, keyset on
    /// <c>(watermark, inventoryId)</c>.
    /// </summary>
    [HttpGet("pos-availability")]
    [ProducesResponseType(typeof(PosAvailabilityPageDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<PosAvailabilityPageDto>> GetPosAvailability(
        [FromQuery] DateTime? since,
        [FromQuery] Guid? sinceId,
        CancellationToken cancellationToken)
    {
        var page = await _feedService.GetPosAvailabilityPageAsync(since, sinceId, cancellationToken);
        return Ok(page);
    }

    /// <summary>
    /// Shop activity feed: every point of sale in one complete reading, no cursor (C43).
    /// </summary>
    /// <remarks>
    /// Takes no query parameters at all — not <c>since</c>, not <c>sinceId</c>, not
    /// <c>pageSize</c> — because the reading is always the whole set. That is what lets the
    /// consumer retire a point of sale that has left the business, which a keyset feed can
    /// never express: a removed row simply stops being emitted.
    /// </remarks>
    [HttpGet("pos-shops")]
    [ProducesResponseType(typeof(PosShopsReadingDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<PosShopsReadingDto>> GetPosShops(
        CancellationToken cancellationToken)
    {
        var reading = await _feedService.GetPosShopsReadingAsync(cancellationToken);
        return Ok(reading);
    }
}
