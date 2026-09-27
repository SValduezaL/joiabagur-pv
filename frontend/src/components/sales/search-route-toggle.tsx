/**
 * Route toggle (C40)
 *
 * Two ways to answer **the same query**, chosen before pressing and with the difference in cost
 * stated up front.
 *
 * This is what makes the ablation of the two retrieval strategies something an operator performs
 * rather than something a report claims. What it is *not* is an A/B test: the operator chooses,
 * so the two populations are selected by whoever chose. The toggle demonstrates the difference;
 * what measures it is the fourth `SearchOrigin` value in the telemetry.
 */

import { Label } from '@/components/ui/label';
import { Zap, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { SearchRoute } from '@/types/ai-search.types';
import { assistedUnavailableText } from '@/components/sales/ai-availability-badge';

/**
 * The cost of each route, in the terms the operator actually feels.
 *
 * Stated **before** pressing and not after, which is the whole point: an operator who discovers
 * the difference by waiting seven seconds has already paid it. The figures are the configured
 * budgets and allowances — 2.500 ms against 10.000 ms, 30/min against 10/min — expressed as time
 * and as a number of searches rather than as milliseconds and permits.
 */
const ROUTE_COST: Record<SearchRoute, string> = {
  semantic: 'Respuesta inmediata · 30 búsquedas por minuto',
  assisted: 'Puede tardar unos segundos · 10 búsquedas por minuto',
};

const ROUTE_LABEL: Record<SearchRoute, string> = {
  semantic: 'Búsqueda rápida',
  assisted: 'Respuesta asistida',
};

interface SearchRouteToggleProps {
  value: SearchRoute;
  onChange: (route: SearchRoute) => void;
  /** Whether the assisted path is switched on for this shop. */
  assistedAvailable: boolean;
  /** Why it is not, when it is not. Shown beside the disabled option. */
  assistedUnavailableReason?: string | null;
  /**
   * Why the fast route cannot serve the current scope, when it cannot (C40_FIX).
   *
   * **A reason of reachability, never of switch.** The fast route does not accept the every-shop
   * scope, which is a different fact from its switch being off, and the caller passes the already
   * written text rather than a flag precisely so the two cannot be conflated here. Saying «semantic
   * search is switched off» when it is not would be the class of false statement this panel exists
   * to stop making.
   */
  semanticUnavailableReason?: string | null;
  /** True when the search covers every shop, so no wording may name one (C40_FIX). */
  scopeIsAllPointsOfSale?: boolean;
  /** True while a search is in flight: changing route mid-search would be confusing. */
  disabled?: boolean;
}

export function SearchRouteToggle({
  value,
  onChange,
  assistedAvailable,
  assistedUnavailableReason,
  semanticUnavailableReason,
  scopeIsAllPointsOfSale = false,
  disabled = false,
}: SearchRouteToggleProps) {
  return (
    <div className="space-y-2" data-testid="search-route-toggle">
      <Label>¿Cómo quieres que te responda?</Label>

      <div
        className="grid gap-2 sm:grid-cols-2"
        role="radiogroup"
        aria-label="Cómo quieres que te responda"
      >
        <RouteOption
          route="semantic"
          selected={value === 'semantic'}
          disabled={disabled || Boolean(semanticUnavailableReason)}
          unavailableReason={semanticUnavailableReason ?? null}
          onSelect={() => onChange('semantic')}
          icon={<Zap className="size-4" aria-hidden />}
        />

        <RouteOption
          route="assisted"
          selected={value === 'assisted'}
          // Disabled with its reason rather than failing when pressed. An option that throws on
          // click is the same lie this whole change exists to remove, moved one step later.
          disabled={disabled || !assistedAvailable}
          unavailableReason={
            assistedAvailable
              ? null
              : assistedUnavailableText(assistedUnavailableReason, scopeIsAllPointsOfSale)
          }
          onSelect={() => onChange('assisted')}
          icon={<Sparkles className="size-4" aria-hidden />}
        />
      </div>
    </div>
  );
}

interface RouteOptionProps {
  route: SearchRoute;
  selected: boolean;
  disabled: boolean;
  onSelect: () => void;
  icon: React.ReactNode;
  unavailableReason?: string | null;
}

function RouteOption({
  route,
  selected,
  disabled,
  onSelect,
  icon,
  unavailableReason,
}: RouteOptionProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      disabled={disabled}
      onClick={onSelect}
      data-testid={`route-option-${route}`}
      className={cn(
        'flex flex-col items-start gap-1 rounded-lg border p-3 text-left transition',
        selected ? 'border-primary bg-primary/5' : 'border-input hover:bg-accent',
        disabled && 'cursor-not-allowed opacity-60 hover:bg-transparent',
      )}
    >
      <span className="flex items-center gap-2 text-sm font-medium">
        {icon}
        {ROUTE_LABEL[route]}
      </span>

      {/* Marked by text and not only by colour, like the origin label of the result row: the
          shop floor is not a place to rely on a border tint. */}
      <span className="text-xs text-muted-foreground">{ROUTE_COST[route]}</span>

      {unavailableReason ? (
        <span className="text-xs font-medium" data-testid={`route-unavailable-${route}`}>
          {unavailableReason}
        </span>
      ) : null}
    </button>
  );
}

export default SearchRouteToggle;
