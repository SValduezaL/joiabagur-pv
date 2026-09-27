/**
 * Assisted Search Result Row (EP14 / C16)
 *
 * A component of its own from day one, on purpose: C36 adds the generated pitch, the citations
 * and the family disambiguation, and it should extend this row rather than rewrite the page.
 */

import { FileText, Package } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { getImageUrl } from '@/lib/image-url';
import type { AssistedSearchResult } from '@/types/ai-search.types';

/**
 * Where the result came from, as the operator reads it.
 *
 * A lookup rather than a conditional so that a later origin — the lexical branch of C21 — is a
 * new entry here instead of a change to the row. An unknown key falls back rather than throwing.
 */
const ORIGIN_LABELS: Record<string, string> = {
  assisted: 'Coincidencia semántica',
  lexical: 'Búsqueda por texto',
};

export function originLabel(origin: string): string {
  return ORIGIN_LABELS[origin] ?? 'Resultado';
}

/** The retriever's name for the semantic branch. `assisted` is the operator's name for it. */
const VECTOR_REASON = 'vector';
const LEXICAL_REASON = 'lexical';

/**
 * Which origin this result has, from its own match reasons — never from whether the assisted
 * path served the response.
 *
 * The distinction matters the moment the embedding provider fails: C21 serves the lexical
 * branch alone with HTTP 200, so a response-wide badge would print "semantic match" over
 * results no semantic search produced. Claiming a capability that did not run is the lie the
 * per-result badge exists to prevent.
 *
 * No match reasons at all means no retriever ran: the search was answered by the .NET side's
 * own degraded text search, which is a text search and says so. A reason this panel does not
 * know falls back to the neutral label rather than guessing.
 */
export function resultOrigin(matchReasons: readonly string[]): string {
  if (matchReasons.includes(VECTOR_REASON)) return 'assisted';
  if (matchReasons.length === 0 || matchReasons.includes(LEXICAL_REASON)) return LEXICAL_REASON;
  return matchReasons[0];
}

/** Which retriever answered the whole search, as far as the results can testify. */
export type SearchOrigin = 'assisted' | 'service-lexical' | 'legacy-lexical' | 'unknown';

/**
 * Which mode the search actually fell into, derived from the results themselves.
 *
 * The browser never talks to the AI service and the response carries no mode field, so this
 * is read from provenance rather than asserted. Three outcomes are distinguishable and worth
 * distinguishing, because the middle one is invisible otherwise:
 *
 * - `assisted` — at least one result came from the semantic branch, so the fused path ran.
 * - `service-lexical` — the AI service answered, but nothing came from the semantic branch.
 *   That is the embedding provider having failed: HTTP 200, results on screen, and the panel
 *   would look perfectly healthy while the capability the screen is named after did not run.
 * - `legacy-lexical` — the assisted path did not serve at all and the .NET side's own text
 *   search answered. Switched off and unavailable arrive identically here, on purpose.
 *
 * With no results there is no provenance to read, so the mode is `unknown` and nothing is
 * claimed about it. That case is already covered by the empty-state messages.
 */
export function searchOrigin(
  results: readonly { matchReasons: string[] }[],
  aiAvailable: boolean,
): SearchOrigin {
  if (!aiAvailable) return 'legacy-lexical';
  if (results.length === 0) return 'unknown';
  return results.some((item) => item.matchReasons.includes(VECTOR_REASON))
    ? 'assisted'
    : 'service-lexical';
}

const euro = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

interface AssistedSearchResultRowProps {
  result: AssistedSearchResult;
  onSelect: (result: AssistedSearchResult) => void;
  /**
   * Opens the sale card for this product (C36).
   *
   * A **secondary** action added to the row rather than a rewrite of it, which is what this
   * component's own docstring anticipated. It neither replaces, disables nor precedes selecting
   * the result for sale.
   *
   * It deliberately does **not** report a selection to the telemetry endpoint: opening a card is
   * not choosing the piece to sell, and counting it as one would inflate the selection rate the
   * search event exists to measure. The selection report stays bound to the act of choosing the
   * product for the sale flow.
   *
   * Optional, so every existing caller and every existing test of this row keeps working
   * unchanged.
   */
  onOpenCard?: (result: AssistedSearchResult) => void;
  /**
   * The shop these figures are about, so the label can name it.
   *
   * `null` or absent means the search was spread over every shop. The row then reports **no**
   * quantity — a zero would assert something false about a piece that may be sitting in the
   * next shop along — and says what to do instead.
   */
  pointOfSaleName?: string | null;
  /**
   * What else this result's family carries, already composed. `null` or absent renders
   * nothing at all — a row padded with a blank line reads as a rendering fault.
   *
   * **A sentence and not a list of actions.** The row announces; the sale card unfolds. An
   * action per sibling here would turn a result list into a variant picker and would let an
   * operator sell a piece they never looked at.
   */
  familyNote?: string | null;
}

export function AssistedSearchResultRow({
  result,
  onSelect,
  onOpenCard,
  pointOfSaleName,
  familyNote,
}: AssistedSearchResultRowProps) {
  const photoUrl = getImageUrl(result.primaryPhotoUrl ?? undefined);

  return (
    <Card data-testid="assisted-search-result">
      <CardContent className="flex items-center gap-4 p-4">
        <div className="relative size-20 shrink-0 overflow-hidden rounded-md bg-muted">
          {photoUrl ? (
            <img src={photoUrl} alt={result.name} className="size-full object-cover" />
          ) : (
            <div className="flex size-full items-center justify-center">
              <Package className="size-8 text-muted-foreground/50" />
            </div>
          )}
        </div>

        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="truncate font-medium">{result.name}</p>
            {/* Rendered only when it exists. C18 populates it; until then there is no size to
                show, and inventing one would be worse than leaving the gap. */}
            {result.variantLabel ? (
              <Badge variant="secondary" appearance="outline">
                Talla {result.variantLabel}
              </Badge>
            ) : null}
          </div>

          <p className="text-sm text-muted-foreground">{result.sku}</p>

          {/* What the grouping hid. The assisted route deduplicates by family, so a ring in
              three sizes takes one row — the right shape for a list, and it drops the fact
              the customer's finger needs. Text only: the row announces, the card unfolds. */}
          {familyNote ? (
            <p className="text-sm text-muted-foreground" data-testid="family-note">
              {familyNote}
            </p>
          ) : null}

          <div className="flex flex-wrap items-center gap-1.5">
            <Badge variant="info" appearance="light">
              {originLabel(resultOrigin(result.matchReasons))}
            </Badge>
            {/* Closes the loop with the quick filters: you filter by silver and you can see that
                the piece is silver. The raw match reasons are still deliberately not rendered:
                since C21 they carry real provenance, but `vector` and `lexical` are engineering
                vocabulary and the badge above is their translation. */}
            {result.materials.map((material) => (
              <Badge key={material} variant="secondary" appearance="outline">
                {material}
              </Badge>
            ))}
          </div>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          <p className="font-semibold">{euro.format(result.price)}</p>

          {/* **Three states and not two.** `hasStock` is null when the search named no shop,
              and `null` is neither «in stock» nor «out of stock»: falling through to the
              warning badge would tell the operator the piece has run out everywhere, which
              is a claim nobody made. */}
          {result.hasStock === null ? (
            <span className="text-sm text-muted-foreground" data-testid="stock-needs-a-shop">
              Selecciona una tienda para ver existencias
            </span>
          ) : result.hasStock ? (
            <span className="text-sm text-muted-foreground" data-testid="stock-label">
              {result.quantityAtPointOfSale} en {pointOfSaleName || 'tienda'}
            </span>
          ) : (
            /* Kept and marked, never hidden: "we carry it, we are out of it" is an answer that
               can still save a sale. Marked by text as well as colour. */
            <Badge variant="warning" appearance="light">
              Sin existencias
            </Badge>
          )}

          <Button size="sm" onClick={() => onSelect(result)}>
            Seleccionar para venta
          </Button>

          {/* Secondary by variant as well as by position: the primary act of this panel is still
              choosing the piece for the sale. Opening the card issues no search, changes no
              result and ends no search episode. */}
          {onOpenCard ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onOpenCard(result)}
              data-testid="assisted-search-open-card"
              /* The card reports one shop's stock and offers its substitutes from that shop's
                 assortment. With no shop chosen it has nothing to answer, so the action is
                 disabled rather than opened onto a card that would degrade.

                 **Read off the data and not off `pointOfSaleName`.** A caller that passes no
                 name is not saying «no shop», it is saying nothing — and keying the guard on
                 the prop would disable the button for every existing caller. `hasStock` is
                 null exactly when the backend answered without a shop, which is the fact
                 this guard is actually about. */
              disabled={result.hasStock === null}
              title={
                result.hasStock === null
                  ? 'Selecciona una tienda para abrir la ficha de venta'
                  : undefined
              }
            >
              <FileText className="mr-1.5 size-3.5" />
              Ver ficha de venta
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

export default AssistedSearchResultRow;
