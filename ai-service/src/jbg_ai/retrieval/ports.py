"""Injectable product-search port. SQL lives in `search`; this file has no I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, Sequence
from uuid import UUID

from jbg_ai.retrieval.lexical import LexicalRequest


@dataclass(frozen=True)
class SearchFilters:
    """Body predicates already parsed. `family_id` is a UUID or absent."""

    materials: list[str] = field(default_factory=list)
    category: str | None = None
    family_id: UUID | None = None
    exclude_product_ids: list[UUID] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """Does this request narrow the catalogue at all?

        Read by the abstention probe of C40 to decide whether a second, unfiltered statement is
        worth issuing: when nothing narrows, the served profile already **is** the unfiltered
        one and a probe would ask the same question twice.

        All four fields count, which is the literal reading of "carries no body filter". It
        includes `exclude_product_ids`, whose effect on a distance profile is negligible — it
        removes a handful of identifiers — so the probe it triggers costs a scan for very
        little. No caller of the orchestrator sets it today (substitutes composes its own
        statement), so the narrow reading costs nothing and the literal one cannot drift from
        the requirement.
        """
        return (
            not self.materials
            and self.category is None
            and self.family_id is None
            and not self.exclude_product_ids
        )


@dataclass(frozen=True)
class SearchHit:
    product_id: UUID
    sku: str
    distance: float
    materials: list[str]
    family_id: UUID | None
    variant_label: str | None
    #: Carried for the demoting filters of C21 and **never** emitted: the boundary rule is
    #: that .NET owns price. A stale projection may reorder a candidate, never delete it.
    price: float | None = None
    size_label: str | None = None
    #: The projection bucket for this point of sale, when the scope was applied. Carried for
    #: the availability demotion and never emitted: an exact stock figure does not exist here
    #: and a bucket on the wire would be the beginning of one. `None` means the query ran
    #: unscoped, which is not the same as a bucket of zero.
    qty_bucket: str | None = None
    #: The drain's own 30-day figure, already counted against the `computed_as_of` recorded
    #: on that projection row and never against the wall clock. `None` means the row was not
    #: read at all — no reading scope, or this point of sale does not carry the product — and
    #: absence is NOT zero sales: no ordering rule may treat it as one.
    sales_30d: int | None = None


@dataclass(frozen=True)
class LexicalHit:
    """One row of a lexical list. `coordination` is how many counting groups it matched."""

    product_id: UUID
    sku: str
    ts_rank: float
    coordination: int
    materials: list[str]
    family_id: UUID | None
    variant_label: str | None
    #: How many counting groups could match any document at all. Constant per query, carried
    #: per row because it is selected in the same statement. `coordination / this` is the
    #: coverage that scales the lexical branch's weight; zero means the query expressed
    #: nothing the index can be asked about, and the caller must not divide by it.
    coverage_denominator: int = 0
    price: float | None = None
    size_label: str | None = None
    qty_bucket: str | None = None
    #: The drain's own 30-day figure, already counted against the `computed_as_of` recorded
    #: on that projection row and never against the wall clock. `None` means the row was not
    #: read at all — no reading scope, or this point of sale does not carry the product — and
    #: absence is NOT zero sales: no ordering rule may treat it as one.
    sales_30d: int | None = None


@dataclass(frozen=True)
class SourceDocument:
    """The reference product a substitutes request is anchored to. C26.

    The embedding itself is NOT carried: the k-NN runs against the stored vector inside the
    statement, so the only thing the caller needs to know here is whether there is one. A
    1.536-float list crossing this boundary would be a copy of a row the database is about
    to read anyway.

    `is_active` and `has_embedding` travel as VALUES and the absent row travels as `None`,
    because the three unusable cases are three different sentences at the boundary and the
    router is what turns them into an error. A port that raised would decide the wording of
    an HTTP response from inside the SQL layer.
    """

    product_id: UUID
    sku: str
    piece_type: str | None
    size_label: str | None
    materials: list[str]
    style_tags: list[str]
    family_id: UUID | None
    price_band: str | None
    is_active: bool
    has_embedding: bool


@dataclass(frozen=True)
class FamilyMember:
    """One member of a product family, as the index holds it. C30a.

    Deliberately **not** a `SearchHit`: there is no query here, so there is no distance and
    no threshold, and inventing either to answer "enumerate this family" would be false.

    It carries **no price and no availability bucket**, and that is the boundary rule rather
    than an oversight: nothing in this dataclass may cross to a `/v1` response, and the two
    fields that must never cross are simply not read.
    """

    product_id: UUID
    sku: str
    variant_label: str | None
    materials: list[str]
    size_label: str | None
    #: Denormalised onto every member row by the projection, so the group's label comes back
    #: with the roster instead of costing a second read of a table this port does not have.
    family_name: str | None = None


@dataclass(frozen=True)
class NeighbourHit:
    """One candidate substitute: a neighbour of a STORED embedding, not of a query. C26.

    It is deliberately not a `SearchHit`. That one answers "what does this query look like",
    is produced with a threshold and a model-compatibility predicate, and carries neither
    `piece_type` nor `style_tags` — the two attributes the substitutes ordering and its
    signals are built on. Widening `SearchHit` to serve both would put four fields nobody
    reads on every row of the product path.

    It satisfies `filters.Constrained` (`price`, `size_label`, `materials`, `qty_bucket`) so
    that `business_score` can be reused unchanged rather than re-derived.
    """

    product_id: UUID
    sku: str
    distance: float
    materials: list[str]
    style_tags: list[str]
    family_id: UUID | None
    variant_label: str | None
    piece_type: str | None
    size_label: str | None
    price_band: str | None = None
    #: Carried for `business_score` and **never** emitted, exactly as on `SearchHit`: .NET
    #: owns price, and a stale projection may reorder a candidate but never delete it.
    price: float | None = None
    #: The projection bucket at the reading point of sale. `None` means the row was not read
    #: — no reading scope, or this point of sale does not carry the product — and absence is
    #: NOT a bucket of zero: no ordering rule may demote on it.
    qty_bucket: str | None = None
    #: The drain's own 30-day figure. `None` is absence and never a zero, as above.
    sales_30d: int | None = None


class ProductSearchPort(Protocol):
    """k-NN and full-text over `ai.product_document`. Implementations must not read `public`.

    The point of sale enters through TWO independent parameters, because restricting the
    universe and reading a signal are different things that one flag used to do at once:

    * `pos_id` RESTRICTS — the C22 prefilter, the only predicate here that removes a
      candidate on availability grounds. `None` means the whole indexed catalogue.
    * `signal_pos_id` only READS — the C25 business signals. It MUST preserve every
      candidate the branches produced, and a product this point of sale does not carry
      reports its signals as absent rather than as zero.

    Both come from a token claim or from the evaluation harness, never from the request body.
    """

    async def count_compatible(self, *, model_version_key: str, model_id: str) -> int: ...

    async def count_scope(self, pos_id: UUID) -> int:
        """Assigned rows this point of sale carries. Zero is a dependency failure."""
        ...

    async def projection_synced_at(self) -> datetime | None:
        """When the POS drain last ran, from the checkpoint — never from `refreshed_at`."""
        ...

    async def scope_buckets(self, pos_id: UUID) -> dict[str, str]:
        """Availability bucket per product for one assortment. Read by the evaluation only.

        The operational metric needs the bucket of every JUDGED document, not only of the
        ones a configuration retrieved, and the response carries no quantity by design — so
        the harness reads the projection rather than inferring it from what came back.
        """
        ...

    async def search(
        self,
        query_vec: list[float],
        *,
        threshold: float,
        depth: int,
        filters: SearchFilters,
        model_version_key: str,
        model_id: str,
        pos_id: UUID | None = None,
        signal_pos_id: UUID | None = None,
    ) -> list[SearchHit]: ...

    async def search_lexical(
        self,
        request: LexicalRequest,
        *,
        depth: int,
        filters: SearchFilters,
        pos_id: UUID | None = None,
        signal_pos_id: UUID | None = None,
    ) -> list[LexicalHit]: ...

    async def source_document(self, product_id: UUID) -> SourceDocument | None:
        """The reference product of a substitutes request, or `None` when no row exists. C26.

        Absence is a RESULT and not an exception, and so are `is_active` and `has_embedding`:
        the three unusable cases — unknown, inactive, unindexed — are one HTTP error each,
        and which sentence a caller writes is not a decision the SQL layer gets to make.
        """
        ...

    async def family_roster(self, family_id: UUID, *, cap: int) -> list[FamilyMember]:
        """Every active member of one family, from `ai.product_document` alone. C30a.

        **Why this is not `search` with a family filter.** That method answers "what does
        this query look like", and answering it costs a query vector, a distance threshold
        and a branch depth. None of the three means anything for "enumerate the members of
        this family": there is no query, so there is no similarity to threshold, and paying
        an embedding for a listing would buy a number nobody reads. Reusing it would also
        make the answer depend on a threshold, which is how a family of four silently starts
        reporting three.

        **Why it exists at all**, rather than being inferred from the candidates already
        retrieved: a product can belong to a family of four and the retrieval return two.
        Grouping cannot know about the members that never came, and the warning that says
        "this family has other variants" is exactly a statement about them. It also serves a
        second real consumer — C32's `listar_familia` tool — which is the bar this project
        sets before extracting a shared piece.

        **Reads only the index schema**, like every other method of this port: never
        `public`, and never the point-of-sale projection. Availability is not read here at
        all, so no bucket can leak into a response through this door.

        `cap` is a **declared** ceiling and not an incidental limit, applied under the same
        order the statement uses. Measured on the live index on 2026-09-13, the largest
        family holds 8 members of 156 families and 491 memberships, so the cap bounds a
        worst case rather than trimming anything real.

        The roster is the index's picture **as of the last sync**. The warning it feeds can
        therefore lag that window, which degrades the advice and never deletes a candidate —
        and asking .NET for it instead would cross the boundary backwards for a fact about
        catalogue structure, which is the index's.
        """
        ...

    async def document_by_sku(self, sku: str) -> SourceDocument | None:
        """The indexed document of one SKU, or `None` when the index holds no such row. C32a.

        **Addressed by SKU and not by product identifier, and that is the whole reason it
        exists** beside `source_document()`, which answers the same question about the same
        table from the other side. The tools of the sale assistant address a piece the way a
        counter does: a SKU is stable, real and semantic, while an internal identifier is an
        arbitrary string of digits nobody says out loud — which is exactly why the generation
        layer already excludes it from everything a model is shown.

        It returns a `SourceDocument` rather than a type of its own because the question is
        the same question: *is there a row, and is it usable?* `is_active` and `has_embedding`
        travel as VALUES and the absent row travels as `None`, by the rule that method already
        fixed — which sentence a caller writes about an unusable piece is not a decision the
        SQL layer gets to make, and here the two callers write different ones.

        Reads `ai.product_document` alone: no projection, no `public`, no provider.
        """
        ...

    async def availability_bucket(self, product_id: UUID, *, pos_id: UUID) -> str | None:
        """The stored availability bucket of ONE piece at ONE point of sale. C32a.

        `None` means **no row was read** — this point of sale does not carry the piece — and
        it is NOT a bucket of zero. The distinction is the same one `SearchHit.qty_bucket`
        already carries, and collapsing it here would report a piece the shop can sell as one
        it cannot.

        **Why not `scope_buckets()`**, which is right there and already reads this table: that
        one returns the point of sale's ENTIRE assortment — of the order of a thousand rows —
        to answer a question about one piece. It exists for an evaluation that needs the
        bucket of every judged document at once; paying its volume per piece would spend a
        connection of a pool capped at five on a dump whose remainder nobody reads.

        The value it returns is a **bucket, and buckets are numerals**. It is deliberately the
        raw stored value and not a label: this is the SQL layer, and translating to the
        qualitative vocabulary here would put a presentation decision inside a port. The
        assistance layer maps it, and nothing between here and there emits it.
        """
        ...

    async def neighbours_of(
        self,
        product_id: UUID,
        *,
        piece_type: str | None,
        depth: int,
        exclude_product_ids: Sequence[UUID] = (),
        signal_pos_id: UUID | None = None,
    ) -> list[NeighbourHit]:
        """Nearest neighbours of a STORED embedding. No provider is called. C26.

        Three predicates remove a candidate and there is no fourth: the hard filter on
        `piece_type`, the source product itself, and whatever the body listed in
        `exclude_product_ids`. A ring is not a second-best pendant, and the piece type is an
        attribute of the indexed catalogue rather than a projection that goes stale, so
        removing on it carries none of the risk that removing on availability would.

        **There is no `pos_id` parameter here, and its absence is the decision.** On the
        product path `pos_id` RESTRICTS and `signal_pos_id` only READS; substitutes offer
        only the second, because availability degrades a candidate and never eliminates it —
        the projection can lag minutes behind the counter, and a page that hid what the shop
        can actually sell would be worse than one that ranks it last. The exclusion by stock
        belongs to .NET, which owns the stock (C34).
        """
        ...
