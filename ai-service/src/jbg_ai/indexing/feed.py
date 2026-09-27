"""Injectable catalog/POS index-feed client. C13 drained catalog only; C22 types the POS side."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol
from uuid import UUID

import httpx

from jbg_ai.indexing.source_text import ProductSourceText
from jbg_ai.indexing.sync_errors import IndexFeedConfigError

CATALOG_PATH = "/api/ai/index-feed/catalog"
POS_PATH = "/api/ai/index-feed/pos-availability"
POS_SHOPS_PATH = "/api/ai/index-feed/pos-shops"
FEED_KEY_HEADER = "X-Index-Feed-Key"
FEED_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class FeedCursor:
    since: datetime
    since_id: UUID


@dataclass(frozen=True)
class CatalogUpsertItem:
    kind: Literal["upsert"]
    product_id: UUID
    source_text: ProductSourceText
    family_id: UUID | None
    price: Decimal
    price_band: str
    is_active: bool
    watermark: datetime


@dataclass(frozen=True)
class CatalogTombstoneItem:
    kind: Literal["tombstone"]
    product_id: UUID
    reason: str
    at: datetime


CatalogFeedItem = CatalogUpsertItem | CatalogTombstoneItem


@dataclass(frozen=True)
class CatalogFeedPage:
    items: list[CatalogFeedItem]
    next_cursor: FeedCursor | None
    has_more: bool
    page_size: int
    aggregate_hash: str


#: The only quantities the feed ever states. An exact stock figure is deliberately absent
#: from the wire, so this vocabulary is the whole of what a consumer can know.
QTY_BUCKETS = frozenset({"0", "1-2", "3+"})

#: The bucket a tombstone leaves behind. Paired with `is_assigned_hint = False` it is the
#: soft delete: the row survives, out of scope and observably unassigned.
TOMBSTONE_BUCKET = "0"

POS_UNASSIGNED_REASON = "unassigned"


@dataclass(frozen=True)
class PosUpsertItem:
    kind: Literal["upsert"]
    point_of_sale_id: UUID
    product_id: UUID
    qty_bucket: str
    is_assigned_hint: bool
    sales_30d: int
    sales_90d: int
    last_sale_at: datetime | None
    watermark: datetime


@dataclass(frozen=True)
class PosTombstoneItem:
    kind: Literal["tombstone"]
    point_of_sale_id: UUID
    product_id: UUID
    reason: str
    at: datetime


PosFeedItem = PosUpsertItem | PosTombstoneItem


@dataclass(frozen=True)
class PosFeedPage:
    items: list[PosFeedItem]
    next_cursor: FeedCursor | None
    has_more: bool
    page_size: int
    aggregate_hash: str
    #: The instant the page's sales windows were counted against. Optional because a feed
    #: older than this field is still a legitimate feed; stored per row when present, since
    #: the feed is incremental and one projection can hold rows counted against several.
    computed_as_of: datetime | None = None


@dataclass(frozen=True)
class PosShopItem:
    """One point of sale and whether it is still trading. C43.

    Carries the identifier and the activity and nothing else: the count this feeds asks how
    many active shops hold no assortment, and a name or a code here would be a second copy of
    a fact `public` owns, going stale between drains with nobody watching it.
    """

    pos_id: UUID
    is_active: bool


@dataclass(frozen=True)
class PosShopsReading:
    """The WHOLE set of points of sale, as of one instant. C43.

    **A reading, not a page, and the distinction is the design.** There is no cursor and no
    `has_more`: a cursored feed can only say what changed, so a point of sale *removed* from
    the business emits nothing and would survive in `ai.pos_shop` for ever. Only a complete
    statement of the set lets the drain retire what is no longer in it.
    """

    items: list[PosShopItem]
    computed_as_of: datetime | None = None


class IndexFeedClient(Protocol):
    """Async port. Implementations must not open sockets unless they are the httpx adapter."""

    async def fetch_catalog_page(
        self, since: datetime | None, since_id: UUID | None
    ) -> CatalogFeedPage: ...

    async def fetch_pos_page(
        self, since: datetime | None, since_id: UUID | None
    ) -> PosFeedPage: ...

    async def fetch_pos_shops(self) -> PosShopsReading: ...


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def _parse_cursor(raw: object) -> FeedCursor | None:
    if not raw or not isinstance(raw, dict):
        return None
    since = raw.get("since")
    since_id = raw.get("sinceId", raw.get("since_id"))
    if since is None or since_id is None:
        return None
    return FeedCursor(since=_parse_datetime(since), since_id=UUID(str(since_id)))


def _as_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def parse_catalog_item(raw: dict[str, object]) -> CatalogFeedItem:
    kind = str(raw.get("kind") or "upsert")
    if kind == "tombstone":
        return CatalogTombstoneItem(
            kind="tombstone",
            product_id=UUID(str(raw["productId"])),
            reason=str(raw.get("reason") or ""),
            at=_parse_datetime(raw["at"]),
        )
    if kind != "upsert":
        raise ValueError(f"unknown catalog feed kind: {kind}")
    source = ProductSourceText(
        sku=str(raw["sku"]),
        name=str(raw["name"]),
        description=_optional_str(raw.get("description")),
        collection_name=_optional_str(raw.get("collectionName")),
        piece_type=_optional_str(raw.get("pieceType")),
        materials=_as_str_list(raw.get("materials")),
        stone_type=_optional_str(raw.get("stoneType")),
        size_label=_optional_str(raw.get("sizeLabel")),
        family_name=_optional_str(raw.get("familyName")),
        variant_label=_optional_str(raw.get("variantLabel")),
        color_tags=_as_str_list(raw.get("colorTags")),
        style_tags=_as_str_list(raw.get("styleTags")),
        occasion_tags=_as_str_list(raw.get("occasionTags")),
    )
    family_raw = raw.get("familyId")
    return CatalogUpsertItem(
        kind="upsert",
        product_id=UUID(str(raw["productId"])),
        source_text=source,
        family_id=UUID(str(family_raw)) if family_raw else None,
        price=Decimal(str(raw.get("price", "0"))),
        price_band=str(raw.get("priceBand") or ""),
        is_active=bool(raw.get("isActive", True)),
        watermark=_parse_datetime(raw["watermark"]),
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_catalog_page(payload: dict[str, object]) -> CatalogFeedPage:
    items_raw = payload.get("items") or []
    if not isinstance(items_raw, list):
        raise ValueError("catalog feed page items must be a list")
    items = [parse_catalog_item(item) for item in items_raw if isinstance(item, dict)]
    return CatalogFeedPage(
        items=items,
        next_cursor=_parse_cursor(payload.get("nextCursor")),
        has_more=bool(payload.get("hasMore", False)),
        page_size=int(payload.get("pageSize") or 0),
        aggregate_hash=str(payload.get("aggregateHash") or ""),
    )


def parse_pos_item(raw: dict[str, object]) -> PosFeedItem:
    """Map one POS feed item onto its typed form.

    An unknown `qtyBucket` is rejected here rather than left for the database's `CHECK` to
    catch: the constraint would abort the batch mid-drain with a message about a constraint
    name, while the vocabulary is a property of the contract and belongs where the contract
    is read.
    """
    kind = str(raw.get("kind") or "upsert")
    if kind == "tombstone":
        return PosTombstoneItem(
            kind="tombstone",
            point_of_sale_id=UUID(str(raw["pointOfSaleId"])),
            product_id=UUID(str(raw["productId"])),
            reason=str(raw.get("reason") or ""),
            at=_parse_datetime(raw["at"]),
        )
    if kind != "upsert":
        raise ValueError(f"unknown POS feed kind: {kind}")

    bucket = str(raw.get("qtyBucket") or "")
    if bucket not in QTY_BUCKETS:
        raise ValueError(f"unknown qtyBucket: {bucket!r}")

    last_sale_at = raw.get("lastSaleAt")
    return PosUpsertItem(
        kind="upsert",
        point_of_sale_id=UUID(str(raw["pointOfSaleId"])),
        product_id=UUID(str(raw["productId"])),
        qty_bucket=bucket,
        is_assigned_hint=bool(raw.get("isAssignedHint", True)),
        sales_30d=int(raw.get("sales30d") or 0),
        sales_90d=int(raw.get("sales90d") or 0),
        last_sale_at=_parse_datetime(last_sale_at) if last_sale_at is not None else None,
        watermark=_parse_datetime(raw["watermark"]),
    )


def parse_pos_page(payload: dict[str, object]) -> PosFeedPage:
    items_raw = payload.get("items") or []
    if not isinstance(items_raw, list):
        raise ValueError("POS feed page items must be a list")
    items = [parse_pos_item(item) for item in items_raw if isinstance(item, dict)]
    computed_as_of = payload.get("computedAsOf")
    return PosFeedPage(
        items=items,
        next_cursor=_parse_cursor(payload.get("nextCursor")),
        has_more=bool(payload.get("hasMore", False)),
        page_size=int(payload.get("pageSize") or 0),
        aggregate_hash=str(payload.get("aggregateHash") or ""),
        computed_as_of=(
            _parse_datetime(computed_as_of) if computed_as_of is not None else None
        ),
    )


def parse_pos_shop_item(raw: dict[str, object]) -> PosShopItem:
    """Map one shop item onto its typed form.

    `isActive` defaults to **True** when absent, matching how `parse_pos_item` reads
    `isAssignedHint`. The default is the safe direction for this particular field: treating an
    unstated shop as active can only ever make the count report a shop as lacking assortment
    that does not, which is a visible alarm somebody investigates — whereas defaulting to
    inactive would silently drop a genuinely broken shop out of the count, which is the exact
    failure this whole capability exists to stop.
    """
    return PosShopItem(
        pos_id=UUID(str(raw["pointOfSaleId"])),
        is_active=bool(raw.get("isActive", True)),
    )


def parse_pos_shops_reading(payload: dict[str, object]) -> PosShopsReading:
    items_raw = payload.get("items") or []
    if not isinstance(items_raw, list):
        raise ValueError("POS shops reading items must be a list")
    items = [parse_pos_shop_item(item) for item in items_raw if isinstance(item, dict)]
    computed_as_of = payload.get("computedAsOf")
    return PosShopsReading(
        items=items,
        computed_as_of=(
            _parse_datetime(computed_as_of) if computed_as_of is not None else None
        ),
    )


def _query_params(since: datetime | None, since_id: UUID | None) -> dict[str, str]:
    if since is None and since_id is None:
        return {}
    params: dict[str, str] = {}
    if since is not None:
        params["since"] = since.isoformat()
    if since_id is not None:
        params["sinceId"] = str(since_id)
    return params


class HttpxIndexFeedClient:
    """httpx adapter. Sends `X-Index-Feed-Key`; never logs the key."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        *,
        catalog_path: str = CATALOG_PATH,
        pos_path: str = POS_PATH,
        pos_shops_path: str = POS_SHOPS_PATH,
    ) -> None:
        self._client = client
        self._api_key = api_key
        self._catalog_path = catalog_path
        self._pos_path = pos_path
        self._pos_shops_path = pos_shops_path

    def _headers(self) -> dict[str, str]:
        return {FEED_KEY_HEADER: self._api_key}

    async def _get_json(
        self,
        path: str,
        since: datetime | None,
        since_id: UUID | None,
        *,
        unavailable: str,
    ) -> dict[str, object]:
        try:
            response = await self._client.get(
                path,
                headers=self._headers(),
                params=_query_params(since, since_id),
            )
        except httpx.TransportError as exc:
            raise IndexFeedConfigError(unavailable) from exc
        if response.status_code >= 500:
            raise IndexFeedConfigError(unavailable)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("feed page must be an object")
        return payload

    async def fetch_catalog_page(
        self, since: datetime | None, since_id: UUID | None
    ) -> CatalogFeedPage:
        payload = await self._get_json(
            self._catalog_path,
            since,
            since_id,
            unavailable="catalog feed is unavailable",
        )
        return parse_catalog_page(payload)

    async def fetch_pos_page(
        self, since: datetime | None, since_id: UUID | None
    ) -> PosFeedPage:
        payload = await self._get_json(
            self._pos_path,
            since,
            since_id,
            unavailable="POS feed is unavailable",
        )
        return parse_pos_page(payload)

    async def fetch_pos_shops(self) -> PosShopsReading:
        # No cursor, so no query parameters: this route states the whole set every time.
        payload = await self._get_json(
            self._pos_shops_path,
            None,
            None,
            unavailable="POS shops feed is unavailable",
        )
        return parse_pos_shops_reading(payload)
