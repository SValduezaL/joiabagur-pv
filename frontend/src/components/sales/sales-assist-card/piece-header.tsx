/**
 * Sale Card — the piece (EP15 / C36)
 *
 * The photo, the name, the SKU, the price and the units this shop holds. Every one of them comes
 * from the catalog and the inventory of that point of sale: nothing here is derived, recomputed
 * or reordered.
 *
 * The one presentation decision is the missing size label, which is rendered **beside the SKU as
 * an attribute of the piece** and never as an alert. See `SIZE_LABEL_MISSING` in the copy table
 * for the measurement behind that.
 */

import { Package } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { getImageUrl } from '@/lib/image-url';
import { SIZE_LABEL_MISSING, warningLabel } from '@/lib/assist-copy';
import type { SalesAssistMember } from '@/types/sales-assist.types';

const euro = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

/** Formats a price in es-ES with the euro sign, as the result row of C16 already does. */
export function formatPrice(price: number): string {
  return euro.format(price);
}

interface PieceHeaderProps {
  /** The anchored member. Exactly one member of the group is. */
  piece: SalesAssistMember;
  /** The warnings the backend emitted, read only for the missing size label. */
  warnings: readonly string[];
  /** Name of the point of sale the card is scoped to, for the units line. */
  pointOfSaleName?: string;
}

export function PieceHeader({ piece, warnings, pointOfSaleName }: PieceHeaderProps) {
  const photoUrl = getImageUrl(piece.primaryPhotoUrl ?? undefined);
  const sizeLabelMissing = warnings.includes(SIZE_LABEL_MISSING);

  return (
    <Card data-testid="assist-piece-header">
      <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-start">
        <div className="relative size-24 shrink-0 overflow-hidden rounded-md bg-muted">
          {photoUrl ? (
            <img src={photoUrl} alt={piece.name} className="size-full object-cover" />
          ) : (
            <div className="flex size-full items-center justify-center">
              <Package className="size-10 text-muted-foreground/50" />
            </div>
          )}
        </div>

        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-semibold tracking-tight">{piece.name}</h2>
            {/* Rendered only when it exists: inventing a size is worse than leaving the gap. */}
            {piece.variantLabel ? (
              <Badge variant="secondary" appearance="outline">
                Talla {piece.variantLabel}
              </Badge>
            ) : null}
          </div>

          <div
            className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground"
            data-testid="assist-piece-attributes"
          >
            <span>{piece.sku}</span>
            {/* An attribute of the piece, beside its SKU — never one of the alerts. It fires on
                58,3 % of cards and is anti-correlated with belonging to a family, so it states
                the enrichment status of the catalog rather than a fact about this piece. It is
                painted every time it arrives: nothing the backend emitted is suppressed. */}
            {sizeLabelMissing ? (
              <>
                <span aria-hidden="true">·</span>
                <span data-testid="assist-size-label-missing">
                  {warningLabel(SIZE_LABEL_MISSING)}
                </span>
              </>
            ) : null}
            {piece.collectionName ? (
              <>
                <span aria-hidden="true">·</span>
                <span>{piece.collectionName}</span>
              </>
            ) : null}
          </div>

          {piece.materials.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {piece.materials.map((material) => (
                <Badge key={material} variant="secondary" appearance="outline">
                  {material}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>

        <div className="flex shrink-0 flex-row items-center gap-3 sm:flex-col sm:items-end">
          <p className="text-lg font-semibold">{formatPrice(piece.price)}</p>

          {piece.hasStock ? (
            <span className="text-sm text-muted-foreground">
              {piece.quantityAtPointOfSale} en {pointOfSaleName || 'esta tienda'}
            </span>
          ) : (
            /* Marked by text as well as by colour, the rule the result row of C16 applies. */
            <Badge variant="warning" appearance="light">
              Sin existencias
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default PieceHeader;
