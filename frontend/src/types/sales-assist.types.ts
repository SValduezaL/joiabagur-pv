/**
 * Sale Assist Types (EP15 / C36)
 *
 * Mirror of the backend contract for `POST /api/ai/products/{productId}/sales-assist` and
 * `GET /api/ai/products/{productId}/substitutes`, both served by C34.
 *
 * Everything the card paints arrives resolved: the argument already has the real price and the
 * real units substituted into it, the group is hydrated against the inventory of that point of
 * sale, the warnings are adjusted to what the shop carries and the substitutes are filtered to
 * what it can sell today. **No field below is derived here and none is invented**: the browser
 * never talks to the AI service, and .NET decides everything about price, stock and availability.
 */

/**
 * State of the argument.
 *
 * Serialized by .NET as the snake_case string (`JsonStringEnumMemberName`), so the wire values
 * are these and not the C# member names. Six values that say six different things; the Spanish
 * for them lives in `lib/assist-copy.ts`, which folds them into five messages without losing the
 * two whose provenance differs.
 */
export type PitchStatus =
  | 'generated'
  | 'ai_unavailable'
  | 'not_generated'
  | 'withheld_by_ai'
  | 'withheld_unresolved'
  | 'withheld_out_of_stock';

/** How a substitutes request ended. Four outcomes, none of them a server error. */
export type SubstitutesOutcome =
  | 'ok'
  | 'none_in_stock'
  | 'product_not_indexed'
  | 'ai_unavailable';

/** What the browser sends to ask for a sale card. */
export interface SalesAssistRequest {
  /** Point of sale the card is served for. Always required — never inferred by the server. */
  pointOfSaleId: string;
  /**
   * The customer's question about the piece, or absent for the piece's own argument.
   *
   * Travels in the body and only in the body. It is free text written about a customer, and a
   * URL is recorded by the proxy's access log, the browser's history and any intermediate cache.
   */
  question?: string;
}

/** One member of a group, hydrated against the point of sale. */
export interface SalesAssistMember {
  productId: string;
  /** SKU as the catalog holds it, never as the index reported it. */
  sku: string;
  name: string;
  /**
   * What tells this variant from its siblings, when known. Null in the 1,7 % of mixed groups,
   * where the row falls back to the SKU rather than leaving itself unidentified.
   */
  variantLabel?: string | null;
  /** Current catalog price, in EUR. */
  price: number;
  /** Units at the point of sale of the request. May be zero. */
  quantityAtPointOfSale: number;
  /**
   * False when the point of sale carries the product and has run out.
   *
   * On the anchored member this is what triggers the substitutes block — never `pitchStatus`,
   * which only reports the absence of stock when no question was asked.
   */
  hasStock: boolean;
  primaryPhotoUrl?: string | null;
  collectionName?: string | null;
  /** Materials from the index, explaining the match. Empty on the degraded path. */
  materials: string[];
  /** Match reasons from the index. Empty on the degraded path. */
  matchReasons: string[];
  /** Whether this is the product the card is anchored to. Exactly one member is. */
  isAnchor: boolean;
}

/** One family, or one product alone, as the card shows it. */
export interface SalesAssistGroup {
  /** Family identifier, or null when the product belongs to none. */
  familyId?: string | null;
  familyLabel?: string | null;
  /** Members the point of sale carries, in the order the backend delivered them. */
  members: SalesAssistMember[];
}

/** A citation as the card shows it. */
export interface SalesAssistCitation {
  /** `<document>#<section>`. Never rendered as the only thing the operator can read. */
  citationId: string;
  documentTitle: string;
  sectionTitle: string;
  /** material, faq, politica, talla. */
  docType: string;
  /**
   * `general` for a fact of the world; `establecimiento` for a commitment of the house, which is
   * confirmed in store before being passed to a customer. The card distinguishes the two both
   * visually and in words.
   */
  claimScope: string;
  snippet: string;
}

/** The sale card of one product at one point of sale. */
export interface SalesAssistResponse {
  /** Whether the AI service served this card. False on every degraded path. */
  aiAvailable: boolean;
  /**
   * Why the AI path degraded, or null when it did not.
   *
   * Six values the backend already computed for its own log and, until C40, discarded:
   * `switched_off`, `credential_rejected`, `not_implemented`, `product_not_indexed`,
   * `ai_unavailable` and `unclassified`. Only one of them changes what the card says — a piece
   * the index has not reached yet fixes itself, so it must not read as an outage.
   */
  degradedReason?: string | null;
  pointOfSaleId: string;
  productId: string;
  /** The AI service's intent, passed through. Null on the degraded path. */
  intent?: string | null;
  /** The anchored product's group, in the order the backend returned it. Never re-sorted here. */
  groups: SalesAssistGroup[];
  /** The argument, resolved. Null in every state but `generated`. */
  pitch?: string | null;
  pitchStatus: PitchStatus;
  /** Corpus fragments the argument used. Empty when degraded. */
  citations: SalesAssistCitation[];
  /**
   * Warning codes, never sentences. The closed vocabulary is translated in `lib/assist-copy.ts`,
   * which is also what keeps a code this screen does not know from breaking a row.
   */
  warnings: string[];
  /**
   * A question back to the operator.
   *
   * **Constant null on these two routes**, and read from the contract rather than removed from
   * it: the AI service's intent classifier runs only in the free-query mode and both routes of
   * C34 are always anchored. It is a field of the transfer object, not a feature, so it is
   * painted if it ever arrives and given no block and no copy of its own.
   */
  clarificationQuestion?: string | null;
  /** Version of the prompt the argument was generated with, when one was. */
  promptVersion?: string | null;
  /** Correlation identifier, to find this request in both services' logs. */
  traceId: string;
}

/** One substitute, hydrated against the point of sale. Always has stock. */
export interface SubstituteResult {
  productId: string;
  sku: string;
  name: string;
  variantLabel?: string | null;
  price: number;
  quantityAtPointOfSale: number;
  primaryPhotoUrl?: string | null;
  collectionName?: string | null;
  materials: string[];
  matchReasons: string[];
  /** Whether the substitute belongs to the same family. */
  familyMatch: boolean;
  /** Share of materials in common, 0 to 1. */
  materialOverlap: number;
  /** Style similarity, 0 to 1. */
  styleSimilarity: number;
}

/** The substitutes of one product that one point of sale can sell today. */
export interface SubstitutesResponse {
  outcome: SubstitutesOutcome;
  /** Substitutes with stock, in the order the AI service ranked them. Never re-sorted here. */
  results: SubstituteResult[];
  /** Candidates the AI service returned. Zero when it did not answer. */
  candidatesReturned: number;
  /** Candidates the point of sale carries, with or without stock. */
  survivedHydration: number;
  pointOfSaleId: string;
  traceId: string;
}

/**
 * How a sale assistance attempt ended, from the card's point of view.
 *
 * Two members the assisted search panel did not need:
 *
 * - `rate-limited`, which the panel already separates and which matters more here: the generative
 *   route allows ten requests per minute per user, and exceeding that budget is the system
 *   protecting itself, not an outage. The operator only has to wait a few seconds.
 * - `not-found`, which on these routes means **this shop does not carry this piece** — C34
 *   answers it before calling the AI at all — and deserves a sentence of its own rather than
 *   reading as a generic failure.
 */
export type SalesAssistOutcome =
  | { kind: 'ok'; response: SalesAssistResponse }
  | { kind: 'rate-limited' }
  | { kind: 'forbidden' }
  | { kind: 'not-found' }
  | { kind: 'invalid'; errors: string[] }
  | { kind: 'error'; message: string };

/** How a substitutes attempt ended. Same members, same reasons. */
export type SubstitutesRequestOutcome =
  | { kind: 'ok'; response: SubstitutesResponse }
  | { kind: 'rate-limited' }
  | { kind: 'forbidden' }
  | { kind: 'not-found' }
  | { kind: 'invalid'; errors: string[] }
  | { kind: 'error'; message: string };

/**
 * The maximum length of the customer's question, as the frozen contract declares it.
 *
 * Checked in the client before sending, so an over-long question costs no request at all. .NET
 * validates the same bound in `SalesAssistRequestValidator`.
 */
export const QUESTION_MAX_LENGTH = 500;
