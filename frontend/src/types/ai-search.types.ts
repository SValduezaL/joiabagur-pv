/**
 * Assisted Search Types (EP14 / C16)
 * Mirror of the backend contract for `POST /api/ai/search` and
 * `POST /api/ai/search-events/{id}/selection`.
 *
 * The browser never talks to the AI service: .NET proposes nothing and decides everything about
 * price, stock and availability, so every field below that describes a product is catalog truth.
 */

// The two the assisted route shares with the sale card of C36, imported rather than restated:
// a second declaration of the same wire shape drifts the first time one of them is corrected.
import type { PitchStatus, SalesAssistCitation } from '@/types/sales-assist.types';

/** What the browser sends to run an assisted search. */
export interface AssistedSearchRequest {
  /** Natural-language query typed by the operator. */
  query: string;
  /**
   * Point of sale the search is served for, never inferred by the server.
   *
   * **Optional on the type, required by this route.** `POST /api/ai/search` still refuses a
   * request with no point of sale, so the panel only omits the field on the assisted route. The
   * field is optional here so that one payload can be built for both routes without a cast;
   * what stops an omission reaching this route is the panel pinning the assisted one whenever
   * the every-shop scope is selected, not the type.
   */
  pointOfSaleId?: string;
  /** How many results to display. The server falls back to its configured default. */
  pageSize?: number;
  /**
   * Groups the reformulations of one visit to the panel, so a rephrasing is not counted as an
   * abandoned query. Generated when the panel mounts, not per search.
   */
  searchSessionId?: string;
  /** Canonical material terms selected in the quick filters. */
  materials?: string[];
  /** Optional piece category. */
  category?: string;
}

/** One result as the operator sees it. */
export interface AssistedSearchResult {
  productId: string;
  sku: string;
  name: string;
  /** Current catalog price, in EUR. */
  price: number;
  /**
   * Units at the point of sale of the search, not the sum across points of sale. `null` when the
   * search named no shop.
   *
   * **Null and zero are different answers.** Zero means the shop carries none; null means nobody
   * asked about a shop, so there is nothing to count — and a zero there would assert something
   * false about a piece that may be sitting in the next shop along.
   */
  quantityAtPointOfSale: number | null;
  /**
   * False when the product is carried by this shop but has run out. Such a result is kept on
   * purpose: "we carry it, we are out of it" is an answer that can still save a sale.
   *
   * `null` with no shop named: whether a piece is in stock is a question about a shop, and
   * answering false would read as «none left» rather than «nobody asked».
   */
  hasStock: boolean | null;
  primaryPhotoUrl?: string | null;
  collectionName?: string | null;
  /** Relevance score from the retriever, or null on the degraded path. */
  score?: number | null;
  /**
   * Which branches of the retriever produced this result — `vector`, `lexical`, or both since
   * C21 fused them. Empty on the degraded path, where no retriever ran and the .NET side's own
   * text search answered.
   *
   * The raw values are still **not rendered**: they are engineering vocabulary. The row
   * translates them into one origin badge per result, which is what lets a search served after
   * an embedding-provider failure say so instead of claiming a semantic match.
   */
  matchReasons: string[];
  /**
   * Materials the retriever recognised. Index signals, not hydrated truth — they explain the
   * match and close the loop with the quick filters. Empty on the degraded path.
   */
  materials: string[];
  familyId?: string | null;
  /**
   * Variant label within the family — the size. Populated by C18, so it is null everywhere
   * today and must be rendered conditionally rather than substituted.
   */
  variantLabel?: string | null;
}

/**
 * The answer to an assisted search.
 *
 * `aiAvailable` and `lowConfidence` are what separate the ways a search can return nothing.
 * They cannot separate "switched off for this shop" from "the AI service is down": both arrive
 * as `aiAvailable: false`. Telemetry distinguishes them server-side; the API does not.
 *
 * `lowConfidence` carries the retriever's cross-branch disagreement signal only when more than
 * one branch ran; when a single branch answered it means what it meant before C21 — nothing was
 * returned. Either way it is only ever read here alongside an empty result list.
 */
export interface AssistedSearchResponse {
  /** Results in the order the retriever ranked them. Never re-sorted on the client. */
  results: AssistedSearchResult[];
  /**
   * Identifier of the recorded search event, so a selection can be attributed to this search.
   * Null when telemetry could not persist, which never fails the search.
   */
  searchEventId?: string | null;
  aiAvailable: boolean;
  lowConfidence: boolean;
  pointOfSaleId: string;
  /** Candidates the retriever produced. Zero on the degraded and disabled paths. */
  candidatesReturned: number;
  /** Candidates that survived hydration at this point of sale. */
  survivedHydration: number;
  /**
   * Filters the operator selected that this search could not apply at all.
   *
   * Empty in every case the endpoint can currently produce — both filters the panel sends are
   * applied on every path. It is read anyway so that a filter added later which the catalog
   * cannot answer is announced instead of ignored, which is the failure this whole change exists
   * to stop making.
   */
  unappliedFilters?: string[];
  /**
   * Codes the retriever emitted about the query itself, from the same closed vocabulary the
   * assisted answer uses. Today only `filters_too_narrow`.
   *
   * **Not the same thing as `unappliedFilters`.** That one names a filter the search could
   * not evaluate at all; this one says every filter was applied and admitted almost nothing,
   * over a query the catalogue can answer. A gap in the searcher against a fact about the
   * operator's own selection, and they end in different actions.
   */
  warnings?: string[];
}

/**
 * Which assisted paths are switched on for one point of sale, read before any search.
 *
 * The panel needs this *before* the operator does anything: `aiAvailable` arrives inside a search
 * response, which is to say afterwards, and by then they have already pressed a button that may
 * have had nothing behind it.
 */
export interface AiSearchAvailability {
  /**
   * The shop the answer is about, or **null** when it is about the scope covering every shop.
   *
   * Null and not a blank identifier, for the same reason the request omits the field rather than
   * blanking it: a blank identifier names no shop, and reading one as «all of them» would turn a
   * client bug into a wider answer.
   */
  pointOfSaleId: string | null;
  /**
   * Whether the semantic path is on. False does not disable anything on screen — the panel still
   * searches, degrading to the lexical searcher with the filters applied — it explains the
   * results rather than preventing them.
   */
  semanticSearchAvailable: boolean;
  /** Whether the generative path is on. False disables the assisted route with its reason. */
  assistedAnswerAvailable: boolean;
  /**
   * Why the assisted answer is unavailable, or null when it is available. Only `switched_off` is
   * knowable without making a call, and this route deliberately makes none.
   */
  assistedAnswerUnavailableReason?: string | null;
  /**
   * Whether the sale agent is on. False disables its entry card with its reason. C42.
   *
   * **A value of its own, never derived from `assistedAnswerAvailable`.** The agent has a credential
   * chain of its own on the service side, so a deployment can have the assisted answer configured
   * and the agent not — and a card that read one for the other would say the agent is available
   * while every agent request came back degraded.
   *
   * Optional, so a response from a backend that predates C42 leaves it undefined rather than false:
   * absent means «the probe did not say», which the card treats as the third state — open, with a
   * warning — and not as «switched off».
   */
  agentAvailable?: boolean;
  /**
   * Why the agent is unavailable, or null when it is. **The agent's own reason and not the assisted
   * answer's**: the two can be off independently, so showing one on the other's card would explain
   * the wrong switch.
   */
  agentUnavailableReason?: string | null;
}

/**
 * How reading availability ended.
 *
 * `unknown` rather than an error state: failing to read the switches must never stop the panel
 * from working. The badge says it could not tell, and the search paths behave as they always did.
 */
export type AiSearchAvailabilityOutcome =
  | { kind: 'ok'; availability: AiSearchAvailability }
  | { kind: 'unknown' };

/**
 * How a search attempt ended, from the panel's point of view.
 *
 * The rate-limit case is a member of its own because the endpoint's contract requires it to stay
 * distinguishable from the AI service being unavailable: one is a fault, the other is the system
 * protecting itself, and they have opposite remedies.
 */
export type SearchFailureOutcome =
  | { kind: 'rate-limited' }
  | { kind: 'forbidden' }
  | { kind: 'invalid'; errors: string[] }
  | { kind: 'error'; message: string };

export type AssistedSearchOutcome =
  | { kind: 'ok'; response: AssistedSearchResponse }
  | SearchFailureOutcome;

/** The four ways the panel can end up with nothing to show, plus the normal one. */
export type AssistedSearchDisplayState =
  | 'results'
  | 'abstained'
  | 'no-assortment'
  | 'degraded'
  | 'rate-limited';

/* -------------------------------------------------------------------------------------------
 * The assisted route of the toggle (C40)
 * ---------------------------------------------------------------------------------------- */

/** One family of the assisted answer, with the members this shop carries. */
export interface FreeQueryGroup {
  familyId: string | null;
  familyLabel: string | null;
  /**
   * Members in the order the service ranked them. Never re-sorted on the client: re-sorting
   * would make the rank measure this code instead of retrieval quality.
   */
  members: AssistedSearchResult[];
}

/**
 * What the assisted answer cost. Present only for an administrator.
 *
 * Inputs of a cost and never the cost: tokens and model, never euros. A tariff written into a
 * screen is wrong the day the provider moves it.
 */
export interface FreeQueryUsage {
  model: string | null;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  promptVersion: string | null;
  aiMs: number | null;
  totalMs: number;
}

/**
 * The answer to a free query.
 *
 * **Sixteen states are reachable, and they are combinations of these fields rather than values
 * of any one of them.** The screen gets them wrong in the combinations, so the table that
 * enumerates them — `Documentos/Proyecto Final AIEng/informes/c40-m1-panel-states.md` — is the
 * thing to read before changing how any of this renders.
 */
export interface FreeQuerySearchResponse {
  groups: FreeQueryGroup[];
  pitch?: string | null;
  pitchStatus: PitchStatus;
  citations: SalesAssistCitation[];
  /**
   * Warning codes about **the query**, never about a piece. The backend filters to these and the
   * screen filters again, which is deliberate rather than redundant.
   */
  warnings: string[];
  /** The question the service asked back, verbatim. Rendered as it arrives and never rewritten. */
  clarificationQuestion?: string | null;
  /**
   * What the router decided. The **only** thing that tells the two no-route states apart, and
   * they need different copy.
   */
  intent?: string | null;
  abstained: boolean;
  aiAvailable: boolean;
  /** Why the AI path degraded, from the closed vocabulary. Null when it did not. */
  degradedReason?: string | null;
  /** Null for anyone but an administrator. */
  usage?: FreeQueryUsage | null;
  searchEventId?: string | null;
  pointOfSaleId?: string | null;
  candidatesReturned: number;
  survivedHydration: number;
  traceId?: string | null;
}

/**
 * How an assisted answer ended, from the panel's point of view.
 *
 * `rate-limited` is a member of its own for the reason the semantic path already holds it apart:
 * exceeding the allowance and the AI being unavailable have **opposite remedies** — one resolves
 * by waiting a few seconds, the other does not resolve by waiting at all — so folding them
 * together would show an outage message to an operator who only has to pause.
 */
export type FreeQuerySearchOutcome =
  | { kind: 'ok'; response: FreeQuerySearchResponse }
  | SearchFailureOutcome;

/**
 * Which route the operator chose for the query they typed.
 *
 * Not persisted anywhere. The default is the cheap one on every visit, because remembering the
 * expensive face is how it gets spent without anybody deciding to.
 */
export type SearchRoute = 'semantic' | 'assisted';

/** What the browser sends to run an assisted answer. */
export interface FreeQuerySearchRequest {
  /** What the operator typed, in their own words. */
  query: string;
  /**
   * The shop to answer about, or **absent** for the scope covering every shop.
   *
   * Absent is not a blank identifier. The route reads the field not being there as the wider
   * scope and refuses a blank one, because what makes that scope safe is that an absent point of
   * sale leaves the availability prefilter unapplied rather than matching every shop.
   */
  pointOfSaleId?: string;
  /** Families wanted. The server falls back to its configured default. */
  pageSize?: number;
  /** The visit this search belongs to, so a rephrasing is not counted as an abandoned query. */
  searchSessionId?: string;
  /** Canonical material terms selected in the quick filters. */
  materials?: string[];
  /** Optional piece category. */
  category?: string;
}
