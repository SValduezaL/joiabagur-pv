/**
 * Sale Card — family disambiguation (EP15 / C36)
 *
 * The block that stops a shop selling the wrong size. When the group carries two or more members
 * this renders **one row and one sale button per member, with nothing preselected**, and offers
 * no sale action that does not name a member. The click *is* the confirmation.
 *
 * That shape, and not a preselected anchor plus a confirmation dialog, because preselect-then-
 * confirm is the pattern people press without reading. There is no component state here at all,
 * which is the point: the guarantee is structural rather than a rule someone has to maintain.
 *
 * Two measurements sustain it. The block fits: **99,6 %** of the 544 groups carry two to four
 * members and the real maximum is six. And the variants are distinguishable: **98,3 %** of the
 * groups carry every label present and distinct, **zero** carry them all null and **zero** carry
 * duplicates. For the remaining 1,7 % — mixed groups — the row falls back to the SKU rather than
 * leaving itself unidentified.
 *
 * With exactly one member there is nothing to choose between, so the direct action returns.
 *
 * The members are rendered in the order the backend delivered them. No sort().
 */

import { Check, Package } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getImageUrl } from '@/lib/image-url';
import { formatPrice } from './piece-header';
import type { SalesAssistGroup, SalesAssistMember } from '@/types/sales-assist.types';

interface MemberRowProps {
  member: SalesAssistMember;
  pointOfSaleName?: string;
  onSell: (member: SalesAssistMember) => void;
}

function MemberRow({ member, pointOfSaleName, onSell }: MemberRowProps) {
  const photoUrl = getImageUrl(member.primaryPhotoUrl ?? undefined);
  /* Degrades to the SKU rather than leaving the row unidentified. A row nobody can tell from
     its neighbour is worse than one identified by a code. */
  const identity = member.variantLabel ?? member.sku;

  return (
    <div
      className="flex items-center gap-3 rounded-md border p-3"
      data-testid="assist-family-member"
      data-product-id={member.productId}
      data-anchor={member.isAnchor ? 'true' : 'false'}
      data-identified-by={member.variantLabel ? 'variant-label' : 'sku'}
    >
      <div className="relative size-12 shrink-0 overflow-hidden rounded bg-muted">
        {photoUrl ? (
          <img src={photoUrl} alt={member.name} className="size-full object-cover" />
        ) : (
          <div className="flex size-full items-center justify-center">
            <Package className="size-5 text-muted-foreground/50" />
          </div>
        )}
      </div>

      <div className="min-w-0 flex-1 space-y-0.5">
        <div className="flex flex-wrap items-center gap-2">
          {/* The variant label is what the operator is choosing between, so it leads the row. */}
          <span className="font-semibold">{identity}</span>
          {member.isAnchor ? (
            <Badge variant="info" appearance="light" data-testid="assist-family-anchor">
              <Check className="me-1 size-3" />
              La que tienes delante
            </Badge>
          ) : null}
        </div>
        <p className="truncate text-sm text-muted-foreground">
          {member.name} · {member.sku}
        </p>
      </div>

      <div className="flex shrink-0 flex-col items-end gap-1.5">
        <span className="font-semibold">{formatPrice(member.price)}</span>
        {member.hasStock ? (
          <span className="text-xs text-muted-foreground">
            {member.quantityAtPointOfSale} en {pointOfSaleName || 'tienda'}
          </span>
        ) : (
          /* Marked by text as well as by colour. */
          <Badge variant="warning" appearance="light">
            Sin existencias
          </Badge>
        )}
        {/* One button per row, and the label names the member: there is no action on this screen
            that starts a sale without saying which variant it is for. */}
        <Button size="sm" disabled={!member.hasStock} onClick={() => onSell(member)}>
          Vender {identity}
        </Button>
      </div>
    </div>
  );
}

interface FamilyBlockProps {
  group: SalesAssistGroup | undefined;
  pointOfSaleName?: string;
  onSell: (member: SalesAssistMember) => void;
}

export function FamilyBlock({ group, pointOfSaleName, onSell }: FamilyBlockProps) {
  const members = group?.members ?? [];

  if (members.length === 0) return null;

  /* One member means there is nothing to choose between — C30a guarantees a null family yields
     exactly one member, so the synthetic group of one can never trigger the confirmation — and
     C34 has already withdrawn the variants warning by this point. */
  if (members.length === 1) {
    const only = members[0];
    return (
      <Card data-testid="assist-family" data-member-count={1}>
        <CardContent className="p-4">
          <Button
            className="w-full sm:w-auto"
            disabled={!only.hasStock}
            onClick={() => onSell(only)}
            data-testid="assist-sell-direct"
          >
            Vender esta pieza
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card data-testid="assist-family" data-member-count={members.length}>
      <CardHeader>
        <CardTitle className="text-base">
          Esta tienda lleva {members.length} variantes{group?.familyLabel ? ` de ${group.familyLabel}` : ''}
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Elige cuál le vendes. Ninguna está seleccionada por defecto.
        </p>
      </CardHeader>
      <CardContent className="space-y-2">
        {/* In the order the backend delivered them. */}
        {members.map((member) => (
          <MemberRow
            key={member.productId}
            member={member}
            pointOfSaleName={pointOfSaleName}
            onSell={onSell}
          />
        ))}
      </CardContent>
    </Card>
  );
}

export default FamilyBlock;
