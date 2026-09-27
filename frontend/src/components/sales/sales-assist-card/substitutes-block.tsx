/**
 * Sale Card — substitutes (EP15 / C36)
 *
 * What to offer when the piece in front of the customer is out of stock here. Four outcomes
 * rendered as four different messages, and the one that matters most is `product_not_indexed`:
 * a state of the catalog that the next synchronisation fixes, told as *"this piece is not ready
 * yet"* and **never** as an outage.
 *
 * A page shorter than the one requested is **declared, not padded**: if three survived, it says
 * three. That is the rule C16 established, and left unsaid a short page reads as the system
 * being unable to search when the shop simply does not carry more.
 *
 * The results are rendered in the order received. No sort().
 */

import { Package, ShoppingBag } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { getImageUrl } from '@/lib/image-url';
import { SUBSTITUTES_NOT_REQUESTED, substitutesMessage } from '@/lib/assist-copy';
import { formatPrice } from './piece-header';
import type { SubstituteResult, SubstitutesResponse } from '@/types/sales-assist.types';

/** What the card knows about its substitutes at any moment. */
export type SubstitutesState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'answered'; response: SubstitutesResponse }
  /** The request was never issued, because the AI path was unavailable for this card. */
  | { kind: 'not-requested' }
  | { kind: 'failed'; message: string };

interface SubstituteRowProps {
  result: SubstituteResult;
  pointOfSaleName?: string;
  onSell: (result: SubstituteResult) => void;
}

function SubstituteRow({ result, pointOfSaleName, onSell }: SubstituteRowProps) {
  const photoUrl = getImageUrl(result.primaryPhotoUrl ?? undefined);

  return (
    <div
      className="flex items-center gap-3 rounded-md border p-3"
      data-testid="assist-substitute"
      data-product-id={result.productId}
    >
      <div className="relative size-12 shrink-0 overflow-hidden rounded bg-muted">
        {photoUrl ? (
          <img src={photoUrl} alt={result.name} className="size-full object-cover" />
        ) : (
          <div className="flex size-full items-center justify-center">
            <Package className="size-5 text-muted-foreground/50" />
          </div>
        )}
      </div>

      <div className="min-w-0 flex-1 space-y-0.5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate font-medium">{result.name}</span>
          {result.familyMatch ? (
            <Badge variant="secondary" appearance="outline">
              Misma familia
            </Badge>
          ) : null}
        </div>
        <p className="truncate text-sm text-muted-foreground">{result.sku}</p>
      </div>

      <div className="flex shrink-0 flex-col items-end gap-1.5">
        <span className="font-semibold">{formatPrice(result.price)}</span>
        <span className="text-xs text-muted-foreground">
          {result.quantityAtPointOfSale} en {pointOfSaleName || 'tienda'}
        </span>
        <Button size="sm" variant="outline" onClick={() => onSell(result)}>
          Vender esta
        </Button>
      </div>
    </div>
  );
}

interface SubstitutesBlockProps {
  state: SubstitutesState;
  pointOfSaleName?: string;
  onSell: (result: SubstituteResult) => void;
}

export function SubstitutesBlock({ state, pointOfSaleName, onSell }: SubstitutesBlockProps) {
  if (state.kind === 'idle') return null;

  if (state.kind === 'not-requested') {
    return (
      <Alert data-testid="assist-substitutes" data-substitutes-state="not-requested">
        <AlertTitle>Sin alternativas que proponer</AlertTitle>
        {/* Not one of the four outcomes: the request was never issued. With the AI path
            unavailable it would come back `ai_unavailable` with certainty, so it is more honest
            to say so than to spend it — and saying nothing would read as a piece with no
            alternatives, which is a different and false claim. */}
        <AlertDescription>{SUBSTITUTES_NOT_REQUESTED}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === 'loading') {
    return (
      <div className="space-y-2" data-testid="assist-substitutes" data-substitutes-state="loading">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  if (state.kind === 'failed') {
    return (
      <Alert variant="destructive" data-testid="assist-substitutes" data-substitutes-state="failed">
        <AlertTitle>No se pudieron buscar alternativas</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  const { response } = state;
  const message = substitutesMessage(response.outcome);
  const results = response.results;
  /* Declared rather than padded, and only when something did come back: with nothing to show,
     the outcome message already says what happened. */
  const shortPage = results.length > 0 && results.length < response.survivedHydration;

  return (
    <Card
      data-testid="assist-substitutes"
      data-substitutes-state="answered"
      data-outcome={response.outcome}
    >
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ShoppingBag className="size-4" />
          {message.title}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{message.body}</p>
      </CardHeader>

      {results.length > 0 ? (
        <CardContent className="space-y-2">
          {/* In the order received. */}
          {results.map((result) => (
            <SubstituteRow
              key={result.productId}
              result={result}
              pointOfSaleName={pointOfSaleName}
              onSell={onSell}
            />
          ))}

          <p className="text-sm text-muted-foreground" data-testid="assist-substitutes-count">
            {results.length === 1
              ? '1 alternativa disponible'
              : `${results.length} alternativas disponibles`}
            {shortPage
              ? ` · ${response.survivedHydration} piezas parecidas en ${pointOfSaleName || 'esta tienda'}`
              : ''}
          </p>
        </CardContent>
      ) : null}
    </Card>
  );
}

export default SubstitutesBlock;
