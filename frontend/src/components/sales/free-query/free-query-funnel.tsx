/**
 * The assisted answer's funnel, for an administrator (C40).
 *
 * **The third of the three infractions the exploration found.** `usage`, `aiMs`, `totalMs` and
 * `model` were computed, paid for and returned, and the screen dropped them: a backend that knew
 * what a request cost and an interface that could not say. This is where they land.
 *
 * Three rules govern what it may show, and each one is a decision rather than a layout choice.
 *
 * **Two times and never one.** `aiMs` against `totalMs` is the only way to tell «the provider was
 * slow» from «we were slow», and those end in opposite work: one is a budget conversation with a
 * vendor, the other is a profiler. A single elapsed figure hides which of the two is happening.
 *
 * **No money, ever.** Tokens and the model name are the *inputs* of a cost, and they are shown. A
 * tariff written into a screen is wrong the day the provider moves it, and the model reported for
 * a multi-stage route names only its last stage — so multiplying it would be false here and
 * inviting the multiplication would spread the falsehood to whoever reads the number.
 *
 * **Neither the query nor the argument.** The funnel is a cost panel, not a transcript. The query
 * is what a customer said and the argument carries it back; both are already excluded from the
 * logs by the same rule, and a diagnostic panel is not a loophole in it.
 */

import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Info } from 'lucide-react';

import { degradedReasonLabel } from '@/lib/assist-copy';
import type { FreeQuerySearchResponse } from '@/types/ai-search.types';

interface FreeQueryFunnelProps {
  response: FreeQuerySearchResponse;
  /** How many rows the screen actually painted, which the response cannot know. */
  displayed: number;
}

/** Milliseconds as an administrator reads them: whole numbers, and seconds once it hurts. */
function elapsed(ms: number | null): string {
  if (ms === null) return '—';
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${Math.round(ms)} ms`;
}

export function FreeQueryFunnel({ response, displayed }: FreeQueryFunnelProps) {
  // Collapsed by default. It is a diagnostic panel on a shop-floor screen, and an administrator
  // serving a customer is an operator with an extra permission, not an auditor.
  const [open, setOpen] = useState(false);
  const usage = response.usage;

  return (
    <div data-testid="assisted-answer-funnel">
      <Button variant="ghost" size="sm" onClick={() => setOpen((value) => !value)}>
        <Info className="mr-1.5 size-3.5" />
        Embudo de la respuesta asistida
      </Button>

      {open ? (
        <div
          className="mt-2 flex flex-wrap gap-2 text-sm text-muted-foreground"
          data-testid="assisted-answer-funnel-body"
        >
          <Badge variant="secondary" appearance="outline">
            Candidatos: {response.candidatesReturned}
          </Badge>
          <Badge variant="secondary" appearance="outline">
            Supervivientes: {response.survivedHydration}
          </Badge>
          <Badge variant="secondary" appearance="outline">
            Mostrados: {displayed}
          </Badge>

          {/* The two times, side by side and labelled, which is the whole point of splitting
              them. `usage` is built by the backend only for an administrator, so its absence
              here is a degraded response rather than a permission problem. */}
          {usage ? (
            <>
              <Badge variant="secondary" appearance="outline" data-testid="funnel-ai-ms">
                IA: {elapsed(usage.aiMs)}
              </Badge>
              <Badge variant="secondary" appearance="outline" data-testid="funnel-total-ms">
                Total: {elapsed(usage.totalMs)}
              </Badge>
              <Badge variant="secondary" appearance="outline" data-testid="funnel-model">
                Modelo: {usage.model ?? '—'}
              </Badge>
              <Badge variant="secondary" appearance="outline" data-testid="funnel-tokens">
                Tokens: {usage.promptTokens} entrada · {usage.completionTokens} salida
              </Badge>
              {usage.promptVersion ? (
                <Badge variant="secondary" appearance="outline">
                  Prompt: {usage.promptVersion}
                </Badge>
              ) : null}
            </>
          ) : null}

          {/* Why the path degraded, when it did. The operator's message says what to do; this
              says which of the six causes it was, which is what a reader of this panel needs. */}
          {response.degradedReason ? (
            <Badge variant="warning" appearance="outline" data-testid="funnel-degraded-reason">
              Degradado: {degradedReasonLabel(response.degradedReason)}
            </Badge>
          ) : null}

          {response.searchEventId ? (
            <Badge variant="secondary" appearance="outline">
              Evento: {response.searchEventId}
            </Badge>
          ) : null}

          {/* Absent on a search spread over every point of sale: that search is not recorded at
              all, because the telemetry table requires a shop. Declared in DEFERRED_TASKS.md,
              and said here so a reader does not take the gap for a telemetry failure. */}
          {!response.searchEventId && response.pointOfSaleId === null ? (
            <Badge variant="secondary" appearance="outline" data-testid="funnel-not-recorded">
              Sin registrar: búsqueda en todas las tiendas
            </Badge>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default FreeQueryFunnel;
