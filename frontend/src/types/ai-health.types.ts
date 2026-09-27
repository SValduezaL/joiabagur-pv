/**
 * Types for the jbg-ai status card on the administrator dashboard (EP11 / C17).
 *
 * The browser cannot ask the AI service directly — it is private by design and publishes no
 * port — so this is the shape the .NET API serves on from `GET /api/ai/health`.
 *
 * Every value here is a state, never a secret: no connection string, no database hostname, no
 * fragment of a credential. `provider` in particular reports whether the embedding key is
 * *configured*, never whether the provider is reachable, which nothing in this system asks.
 */

/** `ok` when the AI service can reach its database; `not_configured` when it has none. */
export type AiHealthDatabaseStatus = 'ok' | 'unavailable' | 'not_configured';

/**
 * `model_mismatch` is the condition worth reading carefully: the service is configured to embed
 * queries with a model other than the one that produced the indexed vectors. Two vector spaces
 * are being compared as if they were one, and the result is noise returned with a 200.
 */
export type AiHealthIndexStatus = 'ok' | 'model_mismatch' | 'unavailable';

/** Presence of the credential. Never its value, and never provider reachability. */
export type AiHealthProviderStatus = 'configured' | 'missing';

export interface AiHealthIndex {
  /** Documents currently indexed. Zero means an empty environment, not a broken one. */
  documents: number;
  /** Model recorded on the index rows, or null when the index is empty. */
  model: string | null;
  /** Model the service is configured to query with. */
  configuredModel: string | null;
  status: AiHealthIndexStatus;
}

/**
 * `never_drained` is kept apart from `stale` because the two need different actions: a
 * projection nobody has ever drained answers 503 to *every* scoped retrieval — while this API
 * degrades correctly to its lexical path and answers 200, so from outside the deployment looks
 * healthy — whereas a stale one serves a wider candidate window and declares it.
 *
 * `unavailable` means the AI service reports the section and could not read it, which is not the
 * same as the section being absent altogether (an older `jbg-ai` image).
 */
export type AiHealthProjectionStatus =
  | 'ok'
  | 'stale'
  | 'never_drained'
  | 'unavailable';

/**
 * Freshness of the point-of-sale availability projection (C41).
 *
 * **The age is the drain's, not a shop's.** Its source holds one row per feed, so every point of
 * sale reports the same number; anything rendered as though it were per-shop would be false.
 *
 * **A stale projection hides nothing.** The backend still applies the truth when it hydrates, so
 * what staleness costs is a short page, never a missing piece — which is why the copy talks about
 * completeness and never about reliability.
 */
export interface AiHealthProjection {
  status: AiHealthProjectionStatus | string;
  /** When the feed was last drained, or null when it never was. */
  syncedAt: string | null;
  fullSyncedAt: string | null;
  /** Seconds since the last drain, or null when it never ran. */
  ageSeconds: number | null;
  /** The ceiling the AI service is configured with, so the verdict can be explained here. */
  ceilingSeconds: number | null;
  /** What the retrieval guard decided. Never recomputed here: that would duplicate the threshold. */
  stale: boolean | null;
  /** Pages recorded as failed for this feed. Cumulative, not "the last run's". */
  failedPages: number | null;
  pointsOfSale: number | null;
  /** Points of sale holding no assortment at all — each one a 503 on every scoped search. */
  shopsWithoutScope: number | null;
}

export interface AiHealthReport {
  status: 'OK' | 'degraded' | string;
  version: string;
  database: AiHealthDatabaseStatus | string;
  index: AiHealthIndex;
  provider: AiHealthProviderStatus | string;
  /**
   * Optional: a deployment can run an older `jbg-ai` image than this API, and a card that threw
   * on the absence would turn a version skew into a broken dashboard.
   */
  projection?: AiHealthProjection | null;
}

/**
 * What the card renders.
 *
 * `unreachable` is a first-class outcome rather than a thrown error: the AI service being down
 * must show as a line on one card, never as a failed dashboard. Everything else on that page —
 * sales, revenue, stock — has nothing to do with the AI and must keep rendering.
 */
export type AiHealthOutcome =
  | { kind: 'ok'; report: AiHealthReport }
  | { kind: 'unreachable'; message: string };
