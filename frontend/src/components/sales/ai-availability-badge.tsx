/**
 * Availability badge (C40)
 *
 * States what the assisted paths can do for this shop **before** the operator searches.
 *
 * The panel could not do this until now: `aiAvailable` travels inside a search response, so the
 * only way to learn that a path was switched off was to use it. That is how a whole project ran
 * on the degraded path without anyone noticing — the screen presented a capability that was off
 * as though it were on, and nothing said otherwise.
 *
 * Two independent switches, so four states, and all four are reachable. The odd one — semantic
 * off, assisted on — is rendered on purpose rather than collapsed into a single "AI" flag, which
 * would describe it wrongly.
 */

import { Badge } from "@/components/ui/badge";
import { Sparkles, TriangleAlert, HelpCircle } from 'lucide-react';
import type { AiSearchAvailability } from '@/types/ai-search.types';

/** Why the assisted answer is off, in Spanish. Falls back to a neutral phrase for an unknown code. */
const UNAVAILABLE_REASONS: Record<string, string> = {
  switched_off: 'La respuesta asistida está desactivada en esta tienda',
};

/**
 * The same reasons, worded for the scope that covers every shop (C40_FIX).
 *
 * A separate table rather than a conditional inside the phrases: in that scope there is no shop to
 * speak of, so «está desactivada **en esta tienda**» is not a wording preference, it is a false
 * statement — and a screen making one of those is exactly what this panel keeps being fixed for.
 */
const UNAVAILABLE_REASONS_ALL_SHOPS: Record<string, string> = {
  switched_off: 'La respuesta asistida está desactivada',
};

/**
 * @param scopeIsAllPointsOfSale True when the search covers every shop, so no wording may name one.
 */
export function assistedUnavailableText(
  reason?: string | null,
  scopeIsAllPointsOfSale = false,
): string {
  const table = scopeIsAllPointsOfSale ? UNAVAILABLE_REASONS_ALL_SHOPS : UNAVAILABLE_REASONS;
  if (!reason) return 'La respuesta asistida no está disponible ahora mismo';
  return table[reason] ?? 'La respuesta asistida no está disponible ahora mismo';
}

interface AiAvailabilityBadgeProps {
  /** Null while it is still being read, or when it could not be read at all. */
  availability: AiSearchAvailability | null;
  /** True once the read has settled, however it settled. */
  settled: boolean;
  /** True when the search covers every shop, so no wording may name one (C40_FIX). */
  scopeIsAllPointsOfSale?: boolean;
}

/**
 * Marked by text as well as by colour, like the origin label of the result row: the shop floor is
 * not a place to rely on a green dot.
 */
export function AiAvailabilityBadge({
  availability,
  settled,
  scopeIsAllPointsOfSale = false,
}: AiAvailabilityBadgeProps) {
  if (!settled) {
    return (
      <Badge variant="secondary" className="gap-1.5" data-testid="ai-availability">
        <Sparkles className="size-3.5" aria-hidden />
        Comprobando disponibilidad…
      </Badge>
    );
  }

  // Read failed. Deliberately not an error: the panel searches perfectly well without knowing
  // this, so announcing a problem would be alarming about something the operator cannot fix and
  // that may not affect them at all.
  if (!availability) {
    return (
      <Badge variant="secondary" className="gap-1.5" data-testid="ai-availability">
        <HelpCircle className="size-3.5" aria-hidden />
        No he podido comprobar la disponibilidad
      </Badge>
    );
  }

  const { semanticSearchAvailable, assistedAnswerAvailable } = availability;

  if (semanticSearchAvailable && assistedAnswerAvailable) {
    return (
      <Badge variant="primary" className="gap-1.5" data-testid="ai-availability">
        <Sparkles className="size-3.5" aria-hidden />
        Búsqueda inteligente y respuesta asistida disponibles
      </Badge>
    );
  }

  if (semanticSearchAvailable && !assistedAnswerAvailable) {
    return (
      <Badge variant="warning" className="gap-1.5" data-testid="ai-availability">
        <TriangleAlert className="size-3.5" aria-hidden />
        Búsqueda inteligente disponible · {assistedUnavailableText(availability.assistedAnswerUnavailableReason, scopeIsAllPointsOfSale)}
      </Badge>
    );
  }

  if (!semanticSearchAvailable && assistedAnswerAvailable) {
    return (
      <Badge variant="warning" className="gap-1.5" data-testid="ai-availability">
        <TriangleAlert className="size-3.5" aria-hidden />
        Búsqueda por texto · Respuesta asistida disponible
      </Badge>
    );
  }

  return (
    <Badge variant="warning" className="gap-1.5" data-testid="ai-availability">
      <TriangleAlert className="size-3.5" aria-hidden />
      Búsqueda por texto · {assistedUnavailableText(availability.assistedAnswerUnavailableReason, scopeIsAllPointsOfSale)}
    </Badge>
  );
}

export default AiAvailabilityBadge;
